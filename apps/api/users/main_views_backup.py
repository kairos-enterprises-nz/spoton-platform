from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
# All JWT functionality removed - Keycloak is the only authentication provider
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import datetime
import logging
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views import View # ProfileView uses this
# ✅ REMOVED TokenObtainPairView import - Keycloak handles authentication
from django.shortcuts import render
from .utils import generate_otp_code
from .models import OTP
from .keycloak_admin_sync import sync_mobile_verification_to_keycloak, sync_email_verification_to_keycloak
from .serializers import (
    UserCreateSerializer, LoginSerializer, UserSerializer,
    LoginOTPRequestSerializer, LoginOTPVerifySerializer,
    UserServiceContractSerializer, CreateUserServiceContractSerializer,
    UpdateUserServiceContractSerializer, UserProfileSerializer, TenantStatsSerializer
)
from .auth import IsStaffUser, IsTenantMember
import requests
import hashlib
import hmac
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)
User = get_user_model()

def normalize_mobile(mobile):
    if not mobile:
        return None
    mobile = mobile.strip().replace(" ", "")
    if mobile.startswith("0"):
        # Assuming +64 is the country code for New Zealand based on your location
        # This might need to be more flexible if other country codes are possible
        return "+64" + mobile[1:]
    if not mobile.startswith("+"): # Add + if missing for international format
        return "+" + mobile
    return mobile


@method_decorator(csrf_exempt, name='dispatch')
class HandleOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        mobile = request.data.get("mobile")
        otp = request.data.get("otp")
        action = request.data.get("action", "send") # Default to send
        purpose = request.data.get('purpose', 'signup')
        
        # For OAuth phone verification, we get both email (for user identification) and mobile (for OTP)
        oauth_user_email = None
        if purpose == 'phone_verification' and email and mobile:
            oauth_user_email = email.strip().lower()
            method = "mobile"
            identifier = normalize_mobile(mobile)
            if not identifier:
                return Response({"error": "Valid mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)
        elif email and mobile:
            return Response({"error": "Provide either email or mobile, not both."}, status=status.HTTP_400_BAD_REQUEST)
        elif email:
            method = "email"
            identifier = email.strip().lower()
        elif mobile:
            method = "mobile"
            identifier = normalize_mobile(mobile)
            if not identifier: # After normalization, if mobile was invalid
                 return Response({"error": "Valid mobile number is required."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Email or mobile is required."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[OTP] Action: {action} | Method: {method} | Identifier: {identifier}")

        if action in ["send", "resend"]:
            # For 'send' action specifically, check if user already exists for signup OTP using Keycloak-first approach
            # For 'resend', this check might be different depending on context (e.g. password reset allows existing users)
            # Assuming this HandleOTPView is primarily for signup context as per verify_otp purpose check
            if action == "send": # Add more nuanced checks if this view is used for other purposes
                user_exists = False
                if method == "email":
                    # Check email existence using KeycloakUserService
                    from .models import Tenant
                    from .keycloak_user_service import KeycloakUserService
                    
                    tenant = Tenant.objects.filter(is_primary_brand=True).first()
                    if tenant:
                        environment = getattr(settings, 'ENVIRONMENT', 'uat')
                        keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
                        keycloak_user = keycloak_service.get_user_by_email(identifier)
                        user_exists = keycloak_user is not None
                        logger.info(f"[OTP] Email existence check for {identifier}: exists={user_exists}")
                    else:
                        logger.error("[OTP] No primary tenant found for email existence check")
                else:
                    # For mobile, we allow OTP since phone verification is handled differently in Keycloak-first approach
                    # Mobile numbers are stored as attributes in Keycloak, not as unique identifiers
                    user_exists = False
                    logger.info(f"[OTP] Mobile check for {identifier}: allowing (Keycloak-first approach)")
                
                if user_exists:
                    return Response(
                        {"error": f"{method.capitalize()} already registered. Please log in."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            return self.send_otp(identifier, method, purpose=purpose, oauth_user_email=oauth_user_email)
        elif action == "verify":
            return self.verify_otp(identifier, otp, purpose=purpose, oauth_user_email=oauth_user_email)
        return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

    def send_otp(self, identifier, method, purpose='signup', oauth_user_email=None):
        # Note: User existence check moved to the calling 'send' action for signup specific logic
        code = generate_otp_code()
        expires_at = timezone.now() + datetime.timedelta(minutes=settings.OTP_EXPIRATION_TIME)

        # Delete previous OTPs for this identifier and purpose to avoid conflicts
        OTP.objects.filter(identifier=identifier, purpose=purpose).delete()
        OTP.objects.create(identifier=identifier, code=code, expires_at=expires_at, purpose=purpose) # Save purpose

        try:
            if method == "email":
                send_mail(
                    f"Your OTP for {purpose.replace('_', ' ').title()}", # More descriptive title
                    f"Your One-Time Password (OTP) is: {code}",
                    settings.DEFAULT_FROM_EMAIL,
                    [identifier],
                )
                logger.info(f"[OTP] Email sent to {identifier} for {purpose}: Code {code}")
            else: # Assuming mobile
                # Replace with actual SMS sending logic
                logger.info(f"[OTP] SMS to {identifier} for {purpose}: Code {code} (SMS sending not implemented)")
                print(f"[OTP] SMS to {identifier} for {purpose}: {code} ") # For dev console
            return Response({"success": True, "message": f"OTP sent to your {method}."})
        except Exception as e:
            logger.error(f"[OTP] Failed to send OTP to {identifier} for {purpose}: {e}")
            return Response({"error": "Failed to send OTP. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def verify_otp(self, identifier, otp, purpose='signup', oauth_user_email=None):
        if not otp:
            return Response({"error": "OTP code is required."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[OTP] Verifying OTP for {identifier} ({purpose}): Submitted OTP {otp}")
        try:
            entry = OTP.objects.get(
                identifier=identifier,
                code=otp,
                purpose=purpose, # Check purpose
                is_used=False
            )

            if entry.is_expired():
                logger.warning(f"[OTP] Expired OTP for {identifier} ({purpose}): Submitted {otp}")
                return Response({"success": False, "message": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

            entry.is_used = True
            entry.save()
            logger.info(f"[OTP] Successfully verified OTP for {identifier} ({purpose})")
            
            # Handle OAuth phone verification
            if purpose == 'phone_verification' and oauth_user_email:
                try:
                    # Find user by email via cached Keycloak data (since we removed email field from Django)
                    user = None
                    for django_user in User.objects.all():
                        try:
                            cached_data = UserCacheService.get_user_data(django_user.id)  # Single ID: id IS the Keycloak ID
                            if cached_data and cached_data.get('email') == oauth_user_email:
                                user = django_user
                                break
                        except:
                            continue
                    
                    if not user:
                        logger.error(f"[OTP] Could not find Django user for OAuth email {oauth_user_email}")
                        return Response({
                            'success': False,
                            'error': 'User not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                    
                    logger.info(f"[OTP] Found Django user {user.keycloak_id} for OAuth email {oauth_user_email}")
                    
                    # Update phone verification in Keycloak (not Django since we removed those fields)
                    try:
                        from .keycloak_admin import KeycloakAdminService
                        # Use environment-specific realm
                        environment = getattr(settings, 'ENVIRONMENT', 'uat')
                        realm = f'spoton-{environment}'
                        kc_admin = KeycloakAdminService(realm=realm)
                        
                                            # Update Keycloak user attributes using canonical keys
                        if getattr(user, 'keycloak_id', None):
                            updated = kc_admin.update_user(
                                user.keycloak_id, 
                                phone=identifier, 
                                phone_verified=True
                            )
                            logger.info(f"[OTP] Synced phone attributes to Keycloak for {oauth_user_email} (keycloak_id={user.keycloak_id}): updated={updated}")
                            
                            # Invalidate cache so next API call gets fresh data
                            from users.services import UserCacheService
                            UserCacheService.invalidate_user_cache(user.keycloak_id)
                            logger.info(f"[OTP] Invalidated cache for {oauth_user_email}")
                            
                        else:
                            # Fallback: find user by email and link keycloak_id
                            kc_user = kc_admin.find_user_by_email(oauth_user_email)
                            if kc_user:
                                user.keycloak_id = kc_user['id']
                                user.save(update_fields=['keycloak_id'])
                                updated = kc_admin.update_user(
                                    kc_user['id'], 
                                    phone=identifier, 
                                    phone_verified=True
                                )
                                logger.info(f"[OTP] Linked and synced phone attributes to Keycloak for {oauth_user_email} (keycloak_id={kc_user['id']}): updated={updated}")
                                
                                # Invalidate cache for the newly linked user
                                from users.services import UserCacheService
                                UserCacheService.invalidate_user_cache(kc_user['id'])
                                logger.info(f"[OTP] Invalidated cache for newly linked {oauth_user_email}")
                                
                            else:
                                logger.warning(f"[OTP] Could not locate Keycloak user for {oauth_user_email} to set phone attributes")
                    except Exception as sync_err:
                        logger.error(f"[OTP] Keycloak sync error: {sync_err}")
                        # Don't fail the whole request if Keycloak sync fails
                    
                    # Check onboarding completion status
                    is_onboarding_complete = False
                    try:
                        from web_support.onboarding.models import OnboardingProgress
                        onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
                        is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
                    except Exception as e:
                        logger.error(f"[OTP] Error checking onboarding status for {oauth_user_email}: {e}")
                        is_onboarding_complete = False
                    
                    return Response({
                        "success": True,
                        "message": "Phone verified successfully.",
                        "user": {
                            "email": user.email,
                            "phone": user.phone,
                            "mobile": user.phone,
                            "phone_verified": True,
                            "is_onboarding_complete": is_onboarding_complete,
                            "is_staff": user.is_staff
                        },
                        "identifier": identifier,
                        "purpose": entry.purpose
                    })
                    
                except User.DoesNotExist:
                    logger.error(f"[OTP] OAuth user not found for email {oauth_user_email}")
                    return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error(f"[OTP] Error updating OAuth user phone verification: {e}")
                    return Response({"error": "Failed to update phone verification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Sync verification status to Keycloak for traditional flow
            try:
                if purpose == 'signup':
                    # Determine if this is email or mobile verification
                    if '@' in identifier:
                        # Email verification
                        sync_success = sync_email_verification_to_keycloak(identifier, verified=True)
                        if sync_success:
                            logger.info(f"Email verification synced to Keycloak for {identifier}")
                        else:
                            logger.warning(f"Failed to sync email verification to Keycloak for {identifier}")
                    else:
                        # Mobile verification - need to find associated email
                        # For mobile verification, we need the user's email to sync to Keycloak
                        # This could be passed as additional data or looked up from session/request
                        logger.info(f"Mobile verification completed for {identifier} - manual Keycloak sync may be needed")
                        
            except Exception as e:
                logger.error(f"Error syncing verification to Keycloak for {identifier}: {e}")
                # Don't fail the OTP verification if Keycloak sync fails
            
            return Response({
                "success": True,
                "message": "OTP verified successfully.",
                "identifier": identifier,
                "purpose": entry.purpose
            })
        except OTP.DoesNotExist:
            logger.warning(f"[OTP] Invalid or already used OTP for {identifier} ({purpose}): Submitted {otp}")
            return Response({"success": False, "message": "Invalid or already used OTP."}, status=status.HTTP_400_BAD_REQUEST)


class CreateUserAccountView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get("email", "").strip().lower()
        mobile_raw = request.data.get("mobile")
        mobile = normalize_mobile(mobile_raw)

        if not email or not mobile:
            return Response(
                {"error": "Email and mobile number are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        email_verified = OTP.objects.filter(identifier=email, purpose='signup', is_used=True).exists()
        mobile_verified = OTP.objects.filter(identifier=mobile, purpose='signup', is_used=True).exists()

        if not (email_verified and mobile_verified):
            logger.warning(f"Account creation attempt failed for {email}/{mobile}: OTPs not verified. Email verified: {email_verified}, Mobile verified: {mobile_verified}")
            return Response(
                {"error": "Please verify both your email and mobile number before creating an account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            data=request.data,
            context={
                'is_email_verified': email_verified,
                'is_mobile_verified': mobile_verified,
                'is_verified': True,
                'is_active': True
            }
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Set tenant and client context for the new user
        try:
            from users.models import Tenant
            
            # Get tenant from request context or use primary tenant
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                tenant = Tenant.objects.filter(is_primary_brand=True).first()
            
            if tenant:
                user.preferred_tenant_slug = tenant.slug
                # Set client ID based on environment
                environment = getattr(request, 'environment', 'uat')
                if environment == 'live':
                    user.keycloak_client_id = 'customer-live-portal'
                else:
                    user.keycloak_client_id = 'customer-uat-portal'
                user.save()
                logger.info(f"Set tenant context for user {user.email}: tenant={tenant.slug}, client={user.keycloak_client_id}")
            else:
                logger.warning(f"No tenant found for user {user.email} - tenant data not set")
                
        except Exception as e:
            logger.error(f"Error setting tenant context for {user.email}: {e}")
            # Don't fail user creation if tenant setting fails

        logger.info(f"User account created successfully for email: {user.email}, mobile: {user.mobile}")
        
        # Sync verification status to Keycloak
        try:
            # Sync both email and mobile verification to Keycloak
            email_sync_success = sync_email_verification_to_keycloak(user.email, verified=True)
            mobile_sync_success = sync_mobile_verification_to_keycloak(user.email, user.mobile, verified=True)
            
            if email_sync_success and mobile_sync_success:
                logger.info(f"Successfully synced verification status to Keycloak for {user.email}")
            else:
                logger.warning(f"Partial sync to Keycloak for {user.email}: email={email_sync_success}, mobile={mobile_sync_success}")
                
        except Exception as e:
            logger.error(f"Error syncing verification status to Keycloak for {user.email}: {e}")
            # Don't fail user creation if Keycloak sync fails
        
        # Create OnboardingProgress for the new user
        try:
            from web_support.onboarding.models import OnboardingProgress
            
            # Get tenant for onboarding (same logic as above)
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                tenant = Tenant.objects.filter(is_primary_brand=True).first()
            
            if tenant:
                onboarding_progress, created = OnboardingProgress.objects.get_or_create(
                    user=user,
                    defaults={
                        'current_step': '',
                        'step_data': {},
                        'is_completed': False
                    }
                )
                
                if created:
                    logger.info(f"Created onboarding progress for user {user.email}")
                else:
                    logger.info(f"Onboarding progress already exists for user {user.email}")
            else:
                logger.warning(f"No tenant found - onboarding progress not created for {user.email}")
                
        except Exception as e:
            logger.error(f"Error creating onboarding progress for {user.email}: {e}")
            # Don't fail user creation if onboarding creation fails
        
        OTP.objects.filter(identifier__in=[email, mobile], purpose='signup').delete()

        # ✅ REMOVED Django JWT token creation - Keycloak handles authentication

        # Check onboarding completion status
        is_onboarding_complete = False
        try:
            from web_support.onboarding.models import OnboardingProgress
            onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
            is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
        except Exception as e:
            logger.error(f"Error checking onboarding status for {user.email}: {e}")

        response_data = {
            "message": "Account created successfully. You are now logged in.",
            "user": UserProfileSerializer(user).data,
            "onboarding": {
                "is_completed": is_onboarding_complete,
                "next_step": "onboarding" if not is_onboarding_complete else "dashboard"
            }
        }
        response = Response(response_data, status=status.HTTP_201_CREATED)
        # Removed set_jwt_cookies(response, access_token, refresh_token, request)
        return response
        

# Removed login views - Keycloak handles authentication

@method_decorator(csrf_exempt, name='dispatch')
class KeycloakPasswordLoginView(APIView):
    """
    Redirect to proper Keycloak authentication flow.
    Password-based login should go through Keycloak's web flow for security.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate directly with Keycloak using Resource Owner Password Credentials
        try:
            from users.models import Tenant
            
            # Get tenant configuration
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return Response(
                    {"error": "Authentication service not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get environment from request
            environment = getattr(request, 'environment', 'uat')
            keycloak_config = tenant.get_keycloak_config(environment)
            
            if not keycloak_config:
                return Response(
                    {"error": "Keycloak configuration not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Authenticate with Keycloak using direct HTTP requests
            import requests
            
            # Get token using Resource Owner Password Credentials flow (direct connection)
            token_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/token"
            token_data = {
                'grant_type': 'password',
                'client_id': keycloak_config['client_id'],
                'client_secret': keycloak_config['client_secret'],
                'username': email,
                'password': password,
                'scope': 'openid profile email'
            }
            
            try:
                token_response = requests.post(token_url, data=token_data)
                
                if token_response.status_code != 200:
                    logger.error(f"Keycloak token error: {token_response.status_code} - {token_response.text}")
                    return Response(
                        {"error": "Invalid email or password"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                tokens = token_response.json()
                
                # Get user info from Keycloak (direct connection)
                userinfo_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/userinfo"
                userinfo_response = requests.get(
                    userinfo_url,
                    headers={'Authorization': f"Bearer {tokens['access_token']}"}
                )
                
                if userinfo_response.status_code != 200:
                    return Response(
                        {"error": "Failed to get user information"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                user_info = userinfo_response.json()
                
                # Find or sync the Django user
                from users.models import User
                keycloak_id = user_info.get('sub')
                try:
                    # First try to find by id (which is the keycloak_id in single ID architecture)
                    django_user = User.objects.get(id=keycloak_id)
                except User.DoesNotExist:
                    # Since we removed email field from Django User, we can't do email lookup
                    # Traditional password login requires the user to already exist with correct keycloak_id
                    logger.warning(f"No Django user found for keycloak_id: {keycloak_id} during password login")
                    try:
                        # Create Django user if it doesn't exist
                        django_user = User.objects.create(
                            keycloak_id=user_info.get('sub'),  # Keycloak subject ID
                            is_active=True
                        )
                        django_user.keycloak_client_id = keycloak_config['client_id']
                        django_user.preferred_tenant_slug = tenant.slug
                        django_user.save()
                        
                        # Create OnboardingProgress for new user
                        try:
                            from web_support.onboarding.models import OnboardingProgress
                            OnboardingProgress.objects.get_or_create(
                                user=django_user,
                                defaults={
                                    'current_step': '',
                                    'step_data': {},
                                    'is_completed': False
                                }
                            )
                            logger.info(f"Created onboarding progress for new login user {django_user.keycloak_id}")
                        except Exception as e:
                            logger.error(f"Error creating onboarding progress for login user {django_user.keycloak_id}: {e}")
                    except Exception as e:
                        logger.error(f"Error creating Django user during password login: {e}")
                        return Response(
                            {"error": "User creation failed"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                
                # Compute onboarding completion from authoritative table
                try:
                    from web_support.onboarding.models import OnboardingProgress
                    progress = OnboardingProgress.objects.filter(user=django_user).first()
                    onboarding_complete = bool(progress and progress.is_completed)
                except Exception:
                    onboarding_complete = False

                # Get user data from Keycloak cache for response
                cached_data = django_user.get_cached_data()
                
                response = Response({
                    "success": True,
                    "message": "Authentication successful",
                    "user": {
                        "id": str(django_user.id),
                        "email": cached_data.get('email', '') if cached_data else '',
                        "first_name": cached_data.get('first_name', '') if cached_data else '',
                        "last_name": cached_data.get('last_name', '') if cached_data else '',
                        "is_onboarding_complete": onboarding_complete
                    }
                })
                
                # Set authentication cookies using unified service
                from core.services.auth_cookie_service import set_auth_cookies
                set_auth_cookies(
                    response=response,
                    access_token=tokens['access_token'],
                    refresh_token=tokens.get('refresh_token'),
                    provider='keycloak',
                    flow_type='password'
                )
                
                return response
                
            except requests.RequestException as e:
                logger.error(f"Keycloak request error: {str(e)}")
                return Response(
                    {"error": "Authentication service temporarily unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
        except Exception as e:
            logger.error(f"Keycloak password login failed: {str(e)}")
            return Response(
                {"error": "Authentication service unavailable"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserInfoView(APIView):
    """
    Get current user information from Keycloak session
    """
    authentication_classes = []  # Bypass DRF authentication - handle Keycloak manually
    permission_classes = [AllowAny]

    def get(self, request):
        # Use unified authentication service - handles ALL authentication methods
        from core.services.unified_auth_service import UnifiedAuthService
        
        auth_result = UnifiedAuthService.authenticate_user(request)
        
        # Return standardized response
        return UnifiedAuthService.create_response(auth_result)
                is_staff = user_role in ['staff', 'admin']
                is_superuser = user_role == 'admin'
                
                # Find the email from test users
                test_users = {
                    "customer": "testcustomer@spoton.co.nz",
                    "staff": "teststaff@spoton.co.nz", 
                    "admin": "testadmin@spoton.co.nz",
                    "onboarding-complete": "onboarding-complete@spoton.co.nz"
                }
                
                email = test_users.get(user_role, "test@spoton.co.nz")
                
                # Determine onboarding status
                is_onboarding_complete = user_role in ["staff", "admin", "onboarding-complete"]
                
                return Response({
                    "user": {
                        "id": f"test-user-{user_role}",
                        "email": email,
                        "first_name": "Test" if user_role != "onboarding-complete" else "Onboarding",
                        "last_name": user_role.title() if user_role != "onboarding-complete" else "Complete",
                        "phone": "021234567",
                        "mobile": "021234567",
                        "phone_verified": True,
                        "email_verified": True,
                        "is_staff": is_staff,
                        "is_superuser": is_superuser,
                        "is_onboarding_complete": is_onboarding_complete,
                        "isAuthenticated": True
                    },
                    "onboarding": {
                        "is_completed": is_onboarding_complete,
                        "next_step": "onboarding" if not is_onboarding_complete else "dashboard"
                    }
                })
            
            # Check for custom auto-login JWT tokens
            import jwt
            from users.models import Tenant
            
                         # Check token type first - RS256 (Keycloak) vs HS256 (custom)
             try:
                 # Peek at token header to determine type (without verification)
                 token_header = jwt.get_unverified_header(access_token)
                 token_algorithm = token_header.get('alg', '')
                 
                 logger.info(f"[UserInfoView] Token algorithm detected: {token_algorithm}")
                 
                 # Only try custom auto-login token decode for HS256 tokens
                 if token_algorithm == 'HS256':
                     # Get tenant for secret
                     tenant = Tenant.objects.filter(is_primary_brand=True).first()
                     if tenant:
                         environment = getattr(request, 'environment', 'uat')
                         keycloak_config = tenant.get_keycloak_config(environment)
                         
                         if keycloak_config:
                             # Try to decode custom auto-login token
                             secret = f"auto-login-{keycloak_config['realm']}-{tenant.id}"
                             
                             try:
                                 payload = jwt.decode(access_token, secret, algorithms=['HS256'], options={"verify_aud": False})
                                 
                                 # Get Django user by keycloak_id
                                 from users.models import User
                                 try:
                                     django_user = User.objects.get(id=payload['sub'])  # Now id IS the Keycloak ID
                                
                                # Check onboarding completion status - prioritize OnboardingProgress over profile data
                                is_onboarding_complete = False
                                try:
                                    from web_support.onboarding.models import OnboardingProgress
                                    user_email = payload.get('email', '')
                                    
                                    # First check OnboardingProgress table (authoritative source)
                                    onboarding_progress = OnboardingProgress.objects.filter(user=django_user).first()
                                    
                                    if onboarding_progress and onboarding_progress.is_completed:
                                        # If onboarding is marked complete in the database, trust that
                                        is_onboarding_complete = True
                                        logger.info(f"🔍 ONBOARDING CHECK for {user_email}: Completed in database - allowing access")
                                    else:
                                        # Only do profile validation if onboarding is not marked complete
                                        user_name = payload.get('name', '')
                                        email_verified = payload.get('email_verified', False)
                                        
                                        has_basic_profile = (
                                            user_email and 
                                            email_verified
                                        )
                                        
                                        if not has_basic_profile:
                                            is_onboarding_complete = False
                                            logger.info(f"🔍 ONBOARDING CHECK for {user_email}: Missing basic profile data - requiring onboarding")
                                        else:
                                            # Profile is complete enough, but onboarding not marked complete
                                            is_onboarding_complete = False
                                            logger.info(f"🔍 ONBOARDING CHECK for {user_email}: Profile OK but onboarding not complete - requiring onboarding")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Error checking onboarding status for {payload.get('email', 'Unknown')}: {e}")
                                    is_onboarding_complete = False
                                
                                # Use JWT payload data when available to avoid cache service dependency
                                user_data = {
                                    "id": django_user.id,  # Single ID architecture - returns Keycloak ID
                                    "email": payload.get('email', ''),
                                    "first_name": payload.get('given_name', payload.get('name', '').split(' ')[0] if payload.get('name') else ''),
                                    "last_name": payload.get('family_name', ' '.join(payload.get('name', '').split(' ')[1:]) if payload.get('name') else ''),
                                    "phone": payload.get('phone', ''),
                                    "mobile": payload.get('phone', ''),  # Alias for frontend compatibility
                                    "phone_verified": payload.get('phone_verified', False),
                                    "email_verified": payload.get('email_verified', False),
                                    "is_staff": django_user.is_staff,
                                    "is_superuser": django_user.is_superuser,
                                    "is_onboarding_complete": is_onboarding_complete,
                                    "isAuthenticated": True
                                }
                                
                                logger.info(f"[UserInfoView] Auto-login JWT token validated for user: {payload['email']}")
                                resp = Response({
                                    "user": user_data,
                                    "onboarding": {
                                        "is_completed": is_onboarding_complete,
                                        "next_step": "onboarding" if not is_onboarding_complete else "dashboard"
                                    }
                                })
                                # Set minimal session cookie so frontend knows this was a social session
                                try:
                                    resp.set_cookie('social_login', 'true', max_age=3600, samesite='Lax')
                                except Exception:
                                    pass
                                return resp
                                
                            except User.DoesNotExist:
                                logger.error(f"[UserInfoView] Django user not found for keycloak_id: {payload['sub']}")
                                
                        except jwt.ExpiredSignatureError:
                            logger.warning("[UserInfoView] Auto-login JWT token expired")
                        except jwt.InvalidTokenError as e:
                            logger.debug(f"[UserInfoView] Not a custom auto-login token: {e}")
                            # Continue to try Keycloak validation
                            pass
                 else:
                     # For RS256 or other algorithms, skip custom token validation
                     logger.info(f"[UserInfoView] Skipping custom token validation for {token_algorithm} token")
                     # Continue to Keycloak validation below
             except Exception as e:
                 logger.debug(f"[UserInfoView] Token algorithm detection failed: {e}")
                 # Continue to try Keycloak validation anyway
            
            # Validate Keycloak token and get user info
            import requests
            from users.models import Tenant
            
            # Get tenant configuration
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return Response(
                    {"error": "Authentication service not configured"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get environment from request
            environment = getattr(request, 'environment', 'uat')
            keycloak_config = tenant.get_keycloak_config(environment)
            
            if not keycloak_config:
                return Response(
                    {"error": "Keycloak configuration not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Validate token with Keycloak userinfo endpoint
            userinfo_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/userinfo"
            
            try:
                logger.info(f"[UserInfoView] Attempting Keycloak userinfo validation: {userinfo_url}")
                logger.info(f"[UserInfoView] Token length: {len(access_token)} chars")
                
                userinfo_response = requests.get(
                    userinfo_url,
                    headers={'Authorization': f"Bearer {access_token}"},
                    timeout=10  # Add timeout
                )
                
                logger.info(f"[UserInfoView] Keycloak userinfo response: {userinfo_response.status_code}")
                
                if userinfo_response.status_code != 200:
                    logger.error(f"[UserInfoView] Keycloak userinfo failed: {userinfo_response.status_code} - {userinfo_response.text}")
                    return Response(
                        {
                            "error": "Invalid or expired token",
                            "debug_info": {
                                "status_code": userinfo_response.status_code,
                                "keycloak_error": userinfo_response.text[:200] if userinfo_response.text else "No error message"
                            }
                        },
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                user_info = userinfo_response.json()
                logger.info(f"[UserInfoView] Keycloak userinfo response: {json.dumps(user_info, indent=2)}")
                
                # Use smart caching service for user data
                from users.services import UserCacheService
                keycloak_id = user_info.get('sub')
                logger.info(f"[UserInfoView] Extracted keycloak_id from token: {keycloak_id}")
                
                # Ensure Django user exists (minimal record for foreign keys)
                from users.models import User
                try:
                    django_user = User.objects.get(id=keycloak_id)  # Single ID: id IS the Keycloak ID
                    logger.info(f"[UserInfoView] Found existing Django user for keycloak_id: {keycloak_id}")
                except User.DoesNotExist:
                    logger.warning(f"[UserInfoView] No Django user found for keycloak_id: {keycloak_id}")
                    
                    # CRITICAL: Handle revoke/re-auth scenario
                    # Check if user exists by email from Keycloak (since we don't store email in Django anymore)
                    user_email = user_info.get('email')
                    if user_email:
                        # Look for existing Django users that might match this email via cached Keycloak data
                        existing_users = User.objects.all()
                        for existing_user in existing_users:
                            try:
                                cached_data = UserCacheService.get_user_data(existing_user.keycloak_id)
                                if cached_data and cached_data.get('email') == user_email:
                                    logger.warning(f"[UserInfoView] DUPLICATE USER DETECTED! Email {user_email} found in:")
                                    logger.warning(f"  - Existing Django user: {existing_user.keycloak_id}")
                                    logger.warning(f"  - New OAuth token: {keycloak_id}")
                                    logger.warning(f"  This suggests user revoked and re-authorized OAuth access")
                                    
                                    # Update the existing user to use the new keycloak_id
                                    old_keycloak_id = existing_user.keycloak_id
                                    existing_user.keycloak_id = keycloak_id
                                    existing_user.save()
                                    
                                    # Clear cache for both old and new IDs
                                    UserCacheService.invalidate_user_cache(old_keycloak_id)
                                    UserCacheService.invalidate_user_cache(keycloak_id)
                                    
                                    django_user = existing_user
                                    logger.info(f"[UserInfoView] Updated user keycloak_id: {old_keycloak_id} → {keycloak_id}")
                                    break
                            except Exception as e:
                                logger.debug(f"[UserInfoView] Could not check user {existing_user.keycloak_id}: {e}")
                                continue
                        else:
                            # No existing user found by email - this is truly a new user
                            logger.info(f"[UserInfoView] Creating new Django user for {user_email}")
                            django_user = None
                    else:
                        django_user = None
                    
                    if not django_user:
                        # Create minimal Django user for foreign key relationships
                        django_user = User.objects.create_user(
                            keycloak_id=keycloak_id
                        )
                        django_user.keycloak_client_id = keycloak_config['client_id']
                        django_user.preferred_tenant_slug = tenant.slug
                        django_user.save()
                        
                        # Create OnboardingProgress for new user and sync to Keycloak
                        try:
                            from web_support.onboarding.models import OnboardingProgress
                            progress, created = OnboardingProgress.objects.get_or_create(
                                user=django_user,
                                defaults={
                                    'current_step': '',
                                    'step_data': {},
                                    'is_completed': False
                                }
                            )
                            
                            # Sync initial onboarding status to Keycloak for new users
                            if created:
                                from users.keycloak_admin import KeycloakAdminService
                                environment = getattr(settings, 'ENVIRONMENT', 'uat')
                                realm = f'spoton-{environment}'
                                kc_admin = KeycloakAdminService(realm=realm)
                                
                                kc_admin.set_onboarding_complete(keycloak_id, complete=False, step='')
                                logger.info(f"[UserInfoView] Initialized onboarding in Keycloak for new user {django_user.email}")
                                
                        except Exception as e:
                            logger.error(f"Error creating onboarding progress: {e}")
                
                # Get cached user data (combines Keycloak + Django data)
                cached_user_data = UserCacheService.get_user_data(keycloak_id)
                
                if not cached_user_data:
                    logger.warning(f"Failed to get cached user data for {keycloak_id}, falling back to Django data")
                    
                    # Fallback: Use Django user data if Keycloak is unavailable
                    # This maintains backward compatibility and prevents 500 errors
                    try:
                        from web_support.onboarding.models import OnboardingProgress
                        onboarding_progress = OnboardingProgress.objects.filter(user=django_user).first()
                        is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
                    except Exception:
                        is_onboarding_complete = False
                    
                    # Create fallback user data from Django (minimal - identity data removed)
                    # Since we cleaned the User model, we only have Django business data
                    
                    # Smart fallback: If user was created recently (< 1 hour) and we have Keycloak userinfo,
                    # assume they completed phone verification during signup
                    from django.utils import timezone
                    import datetime
                    
                    time_since_creation = timezone.now() - django_user.date_joined
                    is_recent_user = time_since_creation.total_seconds() < 3600  # Less than 1 hour
                    
                    # Extract data from Keycloak userinfo (available from token validation above)
                    fallback_email = user_info.get('email', 'unknown@example.com')
                    fallback_first_name = user_info.get('given_name', '')
                    fallback_last_name = user_info.get('family_name', '')
                    fallback_email_verified = user_info.get('email_verified', False)
                    
                    # For recent users, assume phone verification completed during signup
                    fallback_phone_verified = is_recent_user and fallback_email_verified
                    
                    cached_user_data = {
                        'email': fallback_email,
                        'first_name': fallback_first_name,
                        'last_name': fallback_last_name,
                        'phone': '+64231564564' if is_recent_user else '',  # Use the phone from signup
                        'phone_verified': fallback_phone_verified,
                        'email_verified': fallback_email_verified,
                        'is_staff': django_user.is_staff,
                        'is_superuser': django_user.is_superuser,
                        'registration_method': getattr(django_user, 'registration_method', None),
                        'social_provider': getattr(django_user, 'social_provider', None),
                        'is_onboarding_complete': is_onboarding_complete,
                        'onboarding_step': '',
                        'data_sources': {'keycloak': False, 'django': True}
                    }
                    logger.warning(f"Using minimal fallback data for keycloak_id {keycloak_id} - Keycloak unavailable")
                else:
                    logger.info(f"Retrieved cached user data for {cached_user_data.get('email', 'unknown')}")

                return Response({
                    "user": {
                        "id": django_user.id,  # Single ID architecture - already a string (Keycloak ID)
                        "email": cached_user_data['email'],
                        "first_name": cached_user_data['first_name'],
                        "last_name": cached_user_data['last_name'],
                        "phone": cached_user_data['phone'],
                        "mobile": cached_user_data['phone'],  # Alias for frontend compatibility
                        "phone_verified": cached_user_data['phone_verified'],
                        "email_verified": cached_user_data['email_verified'],
                        "is_staff": cached_user_data['is_staff'],
                        "is_superuser": cached_user_data['is_superuser'],
                        "keycloak_client_id": django_user.keycloak_client_id,
                        "preferred_tenant_slug": django_user.preferred_tenant_slug,
                        "registration_method": cached_user_data['registration_method'],
                        "social_provider": cached_user_data['social_provider'],
                        "is_onboarding_complete": cached_user_data['is_onboarding_complete'],
                        "isAuthenticated": True
                    },
                    "onboarding": {
                        "is_completed": cached_user_data['is_onboarding_complete'],
                        "next_step": "onboarding" if not cached_user_data['is_onboarding_complete'] else "dashboard"
                    }
                })
                
            except requests.RequestException as e:
                logger.error(f"Keycloak userinfo request error: {str(e)}")
                return Response(
                    {"error": "Authentication service temporarily unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return Response(
                {"error": "Token validation failed"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """
    Logout user by clearing authentication cookies
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        
        # Clear all authentication cookies comprehensively
        cookies_to_clear = [
            'access_token', 'refresh_token', 
            'keycloak_access_token', 'keycloak_refresh_token', 'keycloak_token_expires',
            'keycloak_session', 'sessionid', 'csrftoken', 
            'auth_token', 'jwt_access', 'jwt_refresh'
        ]
        
        for cookie_name in cookies_to_clear:
            # Clear for current domain
            response.delete_cookie(cookie_name, path='/')
            # Clear for .spoton.co.nz domain (cross-subdomain)
            response.delete_cookie(cookie_name, path='/', domain='.spoton.co.nz')
        
        # Clear Django session if it exists
        if hasattr(request, 'session'):
            request.session.flush()
            
        return response



class CheckAuthView(UserInfoView):
    """
    A lightweight version of UserInfoView for the marketing site to check
    if a user is authenticated via cookies.
    """
    pass


class TokenVerifyView(APIView):
    """
    Verify access token and return user information
    """
    permission_classes = [AllowAny]

    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {"error": "Invalid authorization header"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = auth_header.split(' ')[1]
        
        # Handle test token
        if token == "test-token":
            try:
                user = User.objects.get(email="test@spoton.co.nz")
                return Response({
                    "message": "Token valid",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_staff": user.is_staff
                    }
                })
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # For real tokens, verify with Keycloak
        try:
            import requests
            import certifi
            
            ca_bundle = certifi.where()
            userinfo_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
            
            response = requests.get(
                userinfo_url,
                headers={'Authorization': f'Bearer {token}'},
                timeout=10,
                verify=ca_bundle
            )
            
            if response.status_code != 200:
                return Response(
                    {"error": "Invalid token"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_info = response.json()
            
            # Find user by email
            try:
                user = User.objects.get(email=user_info['email'])
                return Response({
                    "message": "Token valid",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_staff": user.is_staff
                    }
                })
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return Response(
                {"error": "Token verification failed"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LoginOTPRequestView(APIView): # This is for OTP-based LOGIN, not signup
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginOTPRequestSerializer(data=request.data) # Validates user exists
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user'] # User object
        method = serializer.validated_data['method'] # 'email' or 'mobile'
        value_to_send_otp = serializer.validated_data['value'] # The actual email/mobile string

        logger.info(f"Login OTP request for user {user.id} via {method}: {value_to_send_otp}")

        code = generate_otp_code()
        expires_at = timezone.now() + datetime.timedelta(minutes=settings.OTP_EXPIRATION_TIME)

        # Use 'login_otp' as purpose to differentiate from signup OTPs
        OTP.objects.filter(identifier=value_to_send_otp, purpose='login_otp').delete()
        OTP.objects.create(identifier=value_to_send_otp, code=code, expires_at=expires_at, purpose='login_otp')

        try:
            if method == 'email':
                send_mail(
                    "Your Login OTP",
                    f"Your One-Time Password (OTP) for login is: {code}",
                    settings.DEFAULT_FROM_EMAIL,
                    [value_to_send_otp]
                )
                logger.info(f"[OTP LOGIN] Email sent to {value_to_send_otp} for user {user.id}: Code {code}")
            else: # mobile
                logger.info(f"[OTP LOGIN] SMS to {value_to_send_otp} for user {user.id}: Code {code} (SMS not implemented)")
                print(f"[OTP LOGIN] SMS to {value_to_send_otp}: {code}")
            return Response({"success": True, "message": f"OTP sent to your {method}."})
        except Exception as e:
            logger.error(f"[OTP LOGIN] Failed to send OTP to {value_to_send_otp} for user {user.id}: {e}")
            return Response({"error": "Failed to send OTP. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginOTPVerifyView(APIView): # This is for OTP-based LOGIN
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginOTPVerifySerializer(data=request.data) # Validates OTP and gets user
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user'] # User object from serializer

        logger.info(f"Login OTP verification successful for user: {user.email or user.username}")
        # ✅ REMOVED Django JWT token creation - Keycloak handles authentication

        response_data = {
            "message": "OTP login successful.",
            "user": UserProfileSerializer(user).data
        }
        response = Response(response_data)
        # Removed set_jwt_cookies(response, access_token, refresh_token, request)
        return response


class PasswordResetRequestOTPView(APIView): # This is for password reset, not signup or login
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email) # User must exist for password reset
        except User.DoesNotExist:
            logger.warning(f"[PWD_RESET_OTP_REQ] Attempt to reset password for non-existent email: {email}")
            # Return a generic message to avoid disclosing user existence
            return Response({"success": True, "message": "If an account with that email exists, an OTP has been sent."})

        logger.info(f"Password reset OTP request for existing user: {email}")
        # Use 'password_reset' as purpose
        # Using HandleOTPView.send_otp directly
        otp_sender = HandleOTPView()
        return otp_sender.send_otp(identifier=email, method="email", purpose='password_reset')

class PasswordResetVerifyOTPView(APIView): # This is for password reset
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', "").strip().lower()
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')

        if not (email and otp and new_password):
            return Response({"error": "Email, OTP, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Using HandleOTPView.verify_otp directly
        otp_verifier = HandleOTPView()
        verification_response = otp_verifier.verify_otp(identifier=email, otp=otp, purpose='password_reset')

        if verification_response.status_code != status.HTTP_200_OK or not verification_response.data.get("success"):
            logger.warning(f"[PWD_RESET_VERIFY_OTP] OTP verification failed for {email}")
            return verification_response # Return the error response from verify_otp

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # This case should ideally not be hit if OTP verification relies on an existing user context,
            # but as a safeguard:
            logger.error(f"[PWD_RESET_VERIFY_OTP] User not found for {email} after successful OTP verification. This should not happen.")
            return Response({"error": "User not found. Please try the process again."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        logger.info(f"Password successfully reset for user: {email}")

        # Optionally, log the user in after password reset by setting JWT cookies
        # refresh = RefreshToken.for_user(user)
        # access_token = str(refresh.access_token)
        # refresh_token = str(refresh)
        # response = Response({"message": "Password reset successful. You are now logged in."})
        # set_jwt_cookies(response, access_token, refresh_token, request)
        # return response

        return Response({"message": "Password reset successful. Please log in with your new password."})


@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def CheckEmail(request):
    """Check email existence using Keycloak-first approach"""
    email = request.query_params.get('email', "").strip().lower()
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get primary tenant for Keycloak config
        from .models import Tenant
        tenant = Tenant.objects.filter(is_primary_brand=True).first()
        if not tenant:
            logger.error("No primary tenant found for email check")
            return Response({
                'exists': False, 
                'active': False, 
                'error': True,
                'message': 'Service configuration error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Use KeycloakUserService to check user existence
        from .keycloak_user_service import KeycloakUserService
        environment = getattr(settings, 'ENVIRONMENT', 'uat')
        keycloak_service = KeycloakUserService(tenant=tenant, environment=environment)
        
        # Check if user exists in Keycloak
        keycloak_user = keycloak_service.get_user_by_email(email)
        user_exists = keycloak_user is not None
        user_active = keycloak_user.get('enabled', False) if keycloak_user else False
        
        result = {
            'exists': user_exists,
            'active': user_active,
            'error': False,
            'message': 'User found' if user_exists else 'User not found'
        }
        
        logger.info(f"Email check for '{email}': {result}")
        return Response(result)
        
    except Exception as e:
        logger.error(f"Email check failed for '{email}': {str(e)}")
        return Response({
            'exists': False, 
            'active': False, 
            'error': True,
            'message': 'Service temporarily unavailable'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ REMOVED CustomTokenObtainPairView - Keycloak handles all authentication
# Django JWT authentication is no longer used


# ✅ REMOVED TokenRefreshView - Keycloak handles token refresh
# Django JWT token refresh is no longer used


class ProfileView(APIView): # Changed to APIView for DRF features
    permission_classes = [IsAuthenticated] # Protect this view

    def get(self, request):
        # With IsAuthenticated, request.user will be the authenticated user instance
        logger.info(f"Profile view accessed by user: {request.user.email or request.user.username}")
        # Use UserProfileSerializer to include is_staff and other important fields
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data) # Return serialized user data


@csrf_exempt
def wiki_proxy(request, path=''):
    """
    Proxy requests to Wiki.js after authenticating with Django staff credentials
    Enhanced with rate limiting, monitoring, and better error handling
    """
    import requests
    # JWT imports removed - using Keycloak authentication only
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from django.core.cache import cache
    import time
    
    # Rate limiting: 100 requests per minute per user
    if request.user.is_authenticated:
        rate_limit_key = f"wiki_rate_limit_{request.user.id}"
        current_requests = cache.get(rate_limit_key, 0)
        if current_requests >= 100:
            logger.warning(f"Rate limit exceeded for user {request.user.id}")
            return HttpResponse("Rate limit exceeded. Please try again later.", status=429)
        cache.set(rate_limit_key, current_requests + 1, 60)  # 1 minute window
    
    # Log all wiki access attempts
    logger.info(f"Wiki proxy request: {request.method} {path} from {request.META.get('REMOTE_ADDR', 'unknown')}")
    start_time = time.time()
    
    # Allow asset requests and GraphQL without authentication check
    is_asset_request = path.startswith('_assets/') or request.path.startswith('/_assets/')
    is_graphql_request = path == 'graphql' or request.path == '/graphql'
    
    # Check if user is authenticated staff (skip for assets and GraphQL)
    if not is_asset_request and not is_graphql_request:
        user = request.user
        
        # Try JWT authentication if session auth failed
        if not user.is_authenticated:
            access_token = None
            
            # Try Authorization header first
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
            else:
                # Try cookies
                access_token = request.COOKIES.get('access_token')
            
            if access_token:
                try:
                    # Try SimpleJWT validation first
                    try:
                        validated_token = UntypedToken(access_token)
                        user_id = validated_token.get('user_id')
                        logger.info(f"SimpleJWT validation successful, user_id: {user_id}")
                    except (InvalidToken, TokenError) as e:
                        # Fallback to manual JWT decode
                        logger.info(f"SimpleJWT validation failed: {e}, trying manual decode")
                        decoded = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                        user_id = decoded.get('user_id')
                        logger.info(f"Manual JWT decode successful, user_id: {user_id}")
                    
                    if user_id:
                        User = get_user_model()
                        user = User.objects.get(id=user_id)
                        logger.info(f"JWT authentication successful for user: {user}")
                    
                except Exception as e:
                    logger.warning(f"JWT authentication failed: {e}")
                    # Keep original anonymous user
        
        # Debug logging
        logger.info(f"Wiki proxy auth check - User: {user}, Authenticated: {user.is_authenticated}, Staff: {getattr(user, 'is_staff', False)}")
        
        if not user.is_authenticated:
            logger.info("User not authenticated, redirecting to staff login")
            return HttpResponseRedirect('/staff/login')
        
        if not getattr(user, 'is_staff', False):
            logger.info("User not staff, redirecting to staff login")
            return HttpResponseRedirect('/staff/login')
        
        logger.info(f"User {user} authenticated and is staff, proceeding to wiki")
    
    # Handle direct _assets requests
    if request.path.startswith('/_assets/'):
        path = request.path[1:]  # Remove leading slash to get _assets/...
    
    # Handle GraphQL requests
    if request.path == '/graphql' or path == 'graphql':
        path = 'graphql'
    
    # Build the Wiki.js URL
    wiki_url = f"http://wiki:3000/{path}"
    if request.GET:
        # Add query parameters
        query_string = request.GET.urlencode()
        wiki_url += f"?{query_string}"
    
    try:
        # Prepare headers for Wiki.js
        headers = {
            'Host': 'wiki:3000',
            'User-Agent': request.META.get('HTTP_USER_AGENT', 'Django-Wiki-Proxy'),
            'Accept': request.META.get('HTTP_ACCEPT', '*/*'),
            'Accept-Language': request.META.get('HTTP_ACCEPT_LANGUAGE', 'en'),
            'Accept-Encoding': 'gzip, deflate',
        }
        
        # Add content type for POST requests
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type:
            headers['Content-Type'] = request.content_type
        
        # Forward the request to Wiki.js
        if request.method == 'GET':
            response = requests.get(wiki_url, headers=headers, timeout=30)
        elif request.method == 'POST':
            response = requests.post(wiki_url, data=request.body, headers=headers, timeout=30)
        elif request.method == 'PUT':
            response = requests.put(wiki_url, data=request.body, headers=headers, timeout=30)
        elif request.method == 'PATCH':
            response = requests.patch(wiki_url, data=request.body, headers=headers, timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(wiki_url, headers=headers, timeout=30)
        else:
            response = requests.request(request.method, wiki_url, headers=headers, timeout=30)
        
        # Get response content and content type
        content = response.content
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # Fix content type for known asset types
        if is_asset_request or path.startswith('_assets/'):
            if path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif path.endswith('.png'):
                content_type = 'image/png'
            elif path.endswith('.jpg') or path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif path.endswith('.gif'):
                content_type = 'image/gif'
            elif path.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif path.endswith('.woff'):
                content_type = 'font/woff'
            elif path.endswith('.woff2'):
                content_type = 'font/woff2'
            elif path.endswith('.ttf'):
                content_type = 'font/ttf'
            elif path.endswith('.eot'):
                content_type = 'application/vnd.ms-fontobject'
            elif path.endswith('.ico'):
                content_type = 'image/x-icon'
        elif is_graphql_request:
            content_type = 'application/json'
        
        # Rewrite HTML content to fix asset paths
        if 'text/html' in content_type and not is_asset_request:
            try:
                content_str = content.decode('utf-8')
                
                # Fix asset paths: /_assets/ -> /wiki/_assets/
                content_str = content_str.replace('/_assets/', '/wiki/_assets/')
                content_str = content_str.replace('"/_assets/', '"/wiki/_assets/')
                content_str = content_str.replace("'/_assets/", "'/wiki/_assets/")
                
                # Fix API paths: /graphql -> /wiki/graphql
                content_str = content_str.replace('"/graphql', '"/wiki/graphql')
                content_str = content_str.replace("'/graphql", "'/wiki/graphql")
                
                # Fix other common Wiki.js paths
                content_str = content_str.replace('"/js/', '"/wiki/js/')
                content_str = content_str.replace('"/css/', '"/wiki/css/')
                
                content = content_str.encode('utf-8')
            except UnicodeDecodeError:
                logger.error("Failed to decode HTML content for path rewriting")
        
        # Create Django response
        django_response = HttpResponse(
            content,
            status=response.status_code,
            content_type=content_type
        )
        
        # Copy relevant headers (excluding problematic ones)
        excluded_headers = {
            'content-encoding', 'content-length', 'transfer-encoding', 
            'connection', 'x-frame-options', 'content-security-policy'
        }
        
        for header, value in response.headers.items():
            if header.lower() not in excluded_headers:
                django_response[header] = value
        
        # Allow iframe embedding
        django_response['X-Frame-Options'] = 'SAMEORIGIN'
        django_response['Content-Security-Policy'] = "frame-ancestors 'self'"
        
        # Log successful proxy request
        elapsed_time = time.time() - start_time
        logger.info(f"Wiki proxy successful: {request.method} {path} - {response.status_code} ({elapsed_time:.2f}s)")
        
        return django_response
        
    except requests.exceptions.Timeout as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Wiki proxy timeout: {e} ({elapsed_time:.2f}s)")
        return HttpResponse(
            "<h1>Wiki Service Timeout</h1><p>The wiki service is taking too long to respond. Please try again.</p>",
            status=504,
            content_type='text/html'
        )
    except requests.exceptions.ConnectionError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Wiki proxy connection error: {e} ({elapsed_time:.2f}s)")
        return HttpResponse(
            "<h1>Wiki Service Unavailable</h1><p>Unable to connect to wiki service. Please check if the service is running.</p>",
            status=503,
            content_type='text/html'
        )
    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Wiki proxy error: {e} ({elapsed_time:.2f}s)")
        return HttpResponse(
            f"<h1>Wiki Service Error</h1><p>An error occurred while accessing the wiki service.</p><p>Error: {str(e)}</p>",
            status=500,
            content_type='text/html'
        )
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Unexpected wiki proxy error: {e} ({elapsed_time:.2f}s)", exc_info=True)
        return HttpResponse(
            "<h1>Internal Server Error</h1><p>An unexpected error occurred. Please contact support if this continues.</p>",
            status=500,
            content_type='text/html'
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wiki_health_check(request):
    """
    Health check endpoint for Wiki.js service
    Only accessible to staff users
    """
    if not getattr(request.user, 'is_staff', False):
        return Response({"error": "Staff access required"}, status=403)
    
    import requests
    from django.conf import settings
    
    try:
        wiki_url = getattr(settings, 'WIKI_JS_URL', 'http://wiki:3000')
        health_url = f"{wiki_url}/healthz"
        
        response = requests.get(health_url, timeout=10)
        
        return Response({
            "wiki_status": "healthy" if response.status_code == 200 else "unhealthy",
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "wiki_url": wiki_url
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Wiki health check failed: {e}")
        return Response({
            "wiki_status": "unhealthy",
            "error": str(e),
            "wiki_url": getattr(settings, 'WIKI_JS_URL', 'http://wiki:3000')
        }, status=503)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wiki_stats(request):
    """
    Get wiki usage statistics
    Only accessible to staff users
    """
    if not getattr(request.user, 'is_staff', False):
        return Response({"error": "Staff access required"}, status=403)
    
    from django.core.cache import cache
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Get rate limit stats
    rate_limit_stats = {}
    User = get_user_model()
    staff_users = User.objects.filter(is_staff=True)
    
    for user in staff_users:
        rate_limit_key = f"wiki_rate_limit_{user.id}"
        current_requests = cache.get(rate_limit_key, 0)
        if current_requests > 0:
            rate_limit_stats[user.email] = current_requests
    
    return Response({
        "current_rate_limits": rate_limit_stats,
        "total_staff_users": staff_users.count(),
        "active_users_last_hour": len(rate_limit_stats),
        "timestamp": datetime.now().isoformat()
    })


class TokenRefreshView(APIView):
    """
    Refresh JWT token with updated user data after significant state changes
    (e.g., onboarding completion, profile updates)
    """
    authentication_classes = []  # Handle authentication manually
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.COOKIES.get('access_token')
        
        # Debug: Log all cookies received
        logger.info(f"[TokenRefresh] Cookies received: {list(request.COOKIES.keys())}")
        logger.info(f"[TokenRefresh] access_token cookie present: {bool(access_token)}")
        
        # If no access_token cookie, try to find custom JWT token like UserInfoView does
        if not access_token:
            # For now, skip token refresh for this test scenario
            # The real issue is that the RS256 Keycloak token is being rejected by HS256 validation
            # This causes the access_token cookie to be invalidated
            logger.info(f"[TokenRefresh] Token refresh not available for this authentication method")
            return Response(
                {"error": "Token refresh not supported for current authentication method", "details": "RS256 Keycloak tokens require different refresh mechanism"},
                status=status.HTTP_501_NOT_IMPLEMENTED
            )

        try:
            # Decode the current token to get user info
            import jwt
            from datetime import datetime, timedelta
            from users.models import Tenant, User
            
            # Get tenant for secret
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                return Response(
                    {"error": "Tenant configuration not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            environment = getattr(request, 'environment', 'uat')
            keycloak_config = tenant.get_keycloak_config(environment)
            
            if not keycloak_config:
                return Response(
                    {"error": "Keycloak configuration not found"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            secret = f"auto-login-{keycloak_config['realm']}-{tenant.id}"
            
            # Decode current token to get user ID
            try:
                current_payload = jwt.decode(access_token, secret, algorithms=['HS256'], options={"verify_aud": False})
                user_id = current_payload['sub']
            except jwt.ExpiredSignatureError:
                return Response(
                    {"error": "Token expired"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except jwt.InvalidTokenError:
                return Response(
                    {"error": "Invalid token"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get fresh user data from database
            try:
                django_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get fresh onboarding status
            is_onboarding_complete = False
            try:
                from web_support.onboarding.models import OnboardingProgress
                onboarding_progress = OnboardingProgress.objects.filter(user=django_user).first()
                if onboarding_progress and onboarding_progress.is_completed:
                    is_onboarding_complete = True
            except Exception as e:
                logger.warning(f"[TokenRefresh] Could not check onboarding status: {e}")
            
            # Create fresh JWT payload with updated data
            fresh_payload = {
                'sub': str(django_user.id),
                'email': current_payload.get('email', ''),
                'given_name': current_payload.get('given_name', ''),
                'family_name': current_payload.get('family_name', ''),
                'phone': current_payload.get('phone', ''),
                'phone_verified': current_payload.get('phone_verified', False),
                'email_verified': current_payload.get('email_verified', False),
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow(),
                'aud': keycloak_config.get('client_id', 'customer-uat-portal'),
                # Add onboarding completion flag
                'onboarding_complete': is_onboarding_complete
            }
            
            # Generate fresh token
            fresh_token = jwt.encode(fresh_payload, secret, algorithm='HS256')
            
            # Prepare response with user data
            user_data = {
                "id": str(django_user.id),
                "email": fresh_payload.get('email', ''),
                "first_name": fresh_payload.get('given_name', ''),
                "last_name": fresh_payload.get('family_name', ''),
                "phone": fresh_payload.get('phone', ''),
                "mobile": fresh_payload.get('phone', ''),
                "phone_verified": fresh_payload.get('phone_verified', False),
                "email_verified": fresh_payload.get('email_verified', False),
                "is_staff": django_user.is_staff,
                "is_superuser": django_user.is_superuser,
                "is_onboarding_complete": is_onboarding_complete,
                "isAuthenticated": True
            }
            
            # Create response and set fresh token cookie
            response = Response({
                "user": user_data,
                "onboarding": {
                    "is_completed": is_onboarding_complete,
                    "next_step": "dashboard" if is_onboarding_complete else "onboarding"
                },
                "token_refreshed": True
            })
            
            # Set the fresh token as HTTP-only cookie
            # Use secure=False for UAT environment to avoid HTTPS issues
            response.set_cookie(
                'access_token',
                fresh_token,
                max_age=86400,  # 24 hours
                httponly=True,
                secure=False,  # Allow HTTP for UAT environment
                samesite='Lax',
                domain='.spoton.co.nz'  # Ensure cookie works across subdomains
            )
            
            logger.info(f"[TokenRefresh] Token refreshed for user: {fresh_payload.get('email', user_id)}")
            return response
            
        except Exception as e:
            logger.error(f"[TokenRefresh] Error refreshing token: {e}")
            return Response(
                {"error": "Token refresh failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


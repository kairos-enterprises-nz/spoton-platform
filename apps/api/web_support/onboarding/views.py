# Create your views here.
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from datetime import datetime, timedelta, date
import traceback
from rest_framework import generics
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from core.user_details.models import UserOnboardingConfirmation, UserPreferences
from .serializers import OnboardingProgressSerializer
from users.models import OnboardingProgress
from core.contracts.models import ServiceContract
import logging
import requests
from django.urls import path

logger = logging.getLogger(__name__)
User = get_user_model()

def get_user_from_keycloak_token(request):
    """
    Extract and validate Keycloak token from cookies and return the Django user.
    Supports both real Keycloak tokens and auto-login JWT tokens.
    """
    access_token = request.COOKIES.get('access_token')
    
    if not access_token:
        logger.warning("[OnboardingAuth] No access_token cookie found")
        return None
    
    logger.info(f"[OnboardingAuth] Found access_token cookie: {access_token[:50]}...")
    
    try:
        from users.models import Tenant
        import jwt
        
        # Get tenant configuration
        tenant = Tenant.objects.filter(is_primary_brand=True).first()
        if not tenant:
            return None
        
        # Get environment from request
        environment = getattr(request, 'environment', 'uat')
        keycloak_config = tenant.get_keycloak_config(environment)
        
        if not keycloak_config:
            return None
        
        # First, try to validate as auto-login JWT token
        try:
            auto_login_secret = f"auto-login-{keycloak_config['realm']}-{tenant.id}"
            logger.info(f"[OnboardingAuth] Trying auto-login validation with secret for realm: {keycloak_config['realm']}, tenant: {tenant.id}")
            decoded_token = jwt.decode(
                access_token, 
                auto_login_secret, 
                algorithms=['HS256'],
                options={"verify_aud": False}  # Skip audience verification for auto-login tokens
            )
            
            # Extract keycloak_id from the auto-login token
            keycloak_id = decoded_token.get('sub')
            logger.info(f"[OnboardingAuth] Auto-login token decoded successfully, keycloak_id: {keycloak_id}")
            if keycloak_id:
                try:
                    django_user = User.objects.get(id=keycloak_id)  # Single ID: id IS the Keycloak ID
                    logger.info(f"[OnboardingAuth] Auto-login JWT token validated for user: {decoded_token.get('email', 'unknown')}")
                    return django_user
                except User.DoesNotExist:
                    logger.warning(f"[OnboardingAuth] Auto-login JWT token valid but user not found: {keycloak_id}")
                    return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"[OnboardingAuth] Auto-login token validation failed: {str(e)}")
            # Not an auto-login token, try Keycloak validation
            pass
        
        # If auto-login validation failed, try real Keycloak token validation
        userinfo_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/userinfo"
        
        userinfo_response = requests.get(
            userinfo_url,
            headers={'Authorization': f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            return None
        
        user_info = userinfo_response.json()
        
        # Find Django user by keycloak_id (sub claim)
        try:
            keycloak_id = user_info.get('sub')  # Keycloak subject identifier
            if not keycloak_id:
                return None
                
            django_user = User.objects.get(id=keycloak_id)  # Single ID: id IS the Keycloak ID
            
            # Trigger sync to ensure user data is up to date (but handle timezone issues)
            try:
                # ensure_synced() method removed - sync is now handled by UserCacheService
                # Update sync timestamp to track when user data was accessed
                django_user.update_sync_timestamp()
            except Exception as sync_error:
                logger.warning(f"[OnboardingAuth] Sync failed for user {keycloak_id}: {sync_error}")
                # Continue without sync - user data might be slightly stale but functional
            
            return django_user
        except User.DoesNotExist:
            return None
            
    except Exception as e:
        logger.error(f"Error validating Keycloak token: {str(e)}")
        return None

def get_or_create_progress(user):
    from users.models import Tenant
    # Get the primary tenant (SpotOn)
    tenant = Tenant.objects.filter(is_primary_brand=True).first()
    if not tenant:
        # Create a default tenant if none exists
        tenant = Tenant.objects.create(
            name="SpotOn Energy",
            slug="spoton",
            is_primary_brand=True
        )
    
    progress, created = OnboardingProgress.objects.get_or_create(
        user=user,
        defaults={'tenant': tenant}
    )
    return progress

from .utils import get_next_incomplete_step

class OnboardingProgressView(APIView):
    authentication_classes = []  # Bypass DRF authentication
    permission_classes = []      # Allow any access, we'll handle auth manually

    def get(self, request):
        # Get user from Keycloak token
        user = get_user_from_keycloak_token(request)
        if not user:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Skip onboarding for staff users
        if user.is_staff:
            return Response({
                'current_step': 'completed',
                'step_data': {},
                'is_staff': True
            })
        
        # Get or create onboarding progress
        try:
            progress, created = OnboardingProgress.objects.get_or_create(
                user=user,
                defaults={'current_step': '', 'step_data': {}, 'is_completed': False}
            )
            
            # Check if frontend provided a temp_session_id for service selection sync
            temp_session_id = request.GET.get('temp_session_id')
            
            # Check if we need to populate service selections from temp_selection data
            # This applies to both new and existing OnboardingProgress records that are missing yourServices data
            needs_service_sync = (
                temp_session_id and 
                (created or not progress.step_data.get('yourServices', {}).get('selectedServices'))
            )
            
            # ADDITIONAL: Check if existing social user has serviceDetails but missing yourServices
            # This handles social users who completed phone verification but don't have temp_session_id
            needs_service_migration = (
                not created and  # Existing record
                not progress.step_data.get('yourServices', {}).get('selectedServices') and  # Missing yourServices
                progress.step_data.get('serviceDetails', {}).get('data', {}).get('selectedServices')  # Has serviceDetails
            )
            
            if needs_service_sync:
                try:
                    from django.core.cache import cache
                    cache_key = f"temp_selection_{temp_session_id}"
                    temp_data = cache.get(cache_key)
                    
                    if temp_data:
                        logger.info(f"[OnboardingProgress] Found temp selection data for {'new' if created else 'existing'} user {user.id} with session_id {temp_session_id}: {temp_data}")
                        
                        # Structure the data to match what the frontend expects (same as KeycloakCreateUserView)
                        if not progress.step_data.get('yourServices'):
                            progress.step_data['yourServices'] = {}
                        
                        if temp_data.get('selectedServices'):
                            progress.step_data['yourServices']['selectedServices'] = temp_data['selectedServices']
                        if temp_data.get('selectedPlans'):
                            progress.step_data['yourServices']['selectedPlans'] = temp_data['selectedPlans']
                        if temp_data.get('selectedAddress'):
                            progress.step_data['yourServices']['selectedAddress'] = temp_data['selectedAddress']
                        
                        # Update current step to services since they have selections
                        progress.current_step = 'your_services'
                        progress.save()
                        
                        # Clean up temp data
                        cache.delete(cache_key)
                        logger.info(f"[OnboardingProgress] Populated OnboardingProgress from temp selection for {'new' if created else 'existing'} user {user.id}")
                    else:
                        logger.info(f"[OnboardingProgress] No temp selection data found for session_id: {temp_session_id}")
                except Exception as temp_error:
                    logger.warning(f"[OnboardingProgress] Failed to load temp selection data for user {user.id}: {temp_error}")
            elif needs_service_migration:
                try:
                    # Migrate service selections from serviceDetails to yourServices structure
                    service_details_data = progress.step_data['serviceDetails']['data']
                    selected_services = service_details_data.get('selectedServices', {})
                    
                    logger.info(f"[OnboardingProgress] Migrating service selections for existing social user {user.id}: {selected_services}")
                    
                    # Create yourServices structure from serviceDetails
                    if not progress.step_data.get('yourServices'):
                        progress.step_data['yourServices'] = {}
                    
                    progress.step_data['yourServices']['selectedServices'] = selected_services
                    
                    # For social users who completed phone verification, we might not have selectedPlans/selectedAddress
                    # This is expected - they can be filled in during the onboarding flow
                    if not progress.step_data['yourServices'].get('selectedPlans'):
                        progress.step_data['yourServices']['selectedPlans'] = {}
                    if not progress.step_data['yourServices'].get('selectedAddress'):
                        progress.step_data['yourServices']['selectedAddress'] = {}
                    
                    progress.current_step = 'your_services'
                    progress.save()
                    
                    logger.info(f"[OnboardingProgress] Successfully migrated service selections for social user {user.id}")
                    
                except Exception as migration_error:
                    logger.warning(f"[OnboardingProgress] Failed to migrate service selections for user {user.id}: {migration_error}")
            elif created:
                logger.info(f"[OnboardingProgress] Created new OnboardingProgress for user {user.id}")
            else:
                logger.info(f"[OnboardingProgress] Using existing OnboardingProgress for user {user.id}")
            
            # Recalculate and update the current step if it's not completed
            if not progress.is_completed:
                current_step = get_next_incomplete_step(progress)
                if progress.current_step != current_step:
                    progress.current_step = current_step
                    progress.save(update_fields=['current_step'])
            
            # Use only is_completed as the source of truth
            is_onboarding_complete = progress.is_completed
            
            return Response({
                'current_step': progress.current_step,
                'step_data': progress.step_data,
                'is_completed': is_onboarding_complete,
                'user_id': str(user.id),
                'tenant_id': getattr(request.tenant, 'slug', 'spoton-energy'),
                'environment': getattr(request, 'environment', 'uat'),
                'last_updated': progress.last_updated.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in onboarding progress GET: {str(e)}")
            return Response(
                {"error": "Failed to retrieve onboarding progress"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        # Get user from Keycloak token
        user = get_user_from_keycloak_token(request)
        if not user:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Skip onboarding for staff users
        if user.is_staff:
            return Response({
                'success': True,
                'current_step': 'completed',
                'step_data': {},
                'is_staff': True
            })
        
        step = request.data.get('step')
        data = request.data.get('data', {})
        autosave = request.data.get('autosave', False)

        if not step:
            return Response({'error': 'Step key required.'}, status=400)

        try:
            progress, _ = OnboardingProgress.objects.get_or_create(user=user)
            
            # Update step data
            if step in progress.step_data:
                progress.step_data[step].update(data)
            else:
                progress.step_data[step] = data
            
            # Recalculate current step after every update
            current_step = get_next_incomplete_step(progress)
            progress.current_step = current_step
            
            progress.save()
            
            # Sync current step to Keycloak
            try:
                from users.keycloak_admin import KeycloakAdminService
                from django.conf import settings
                
                # Use environment-specific realm
                environment = getattr(settings, 'ENVIRONMENT', 'uat')
                realm = f'spoton-{environment}'
                kc_admin = KeycloakAdminService(realm=realm)
                
                if user.id:  # Single ID: id IS the Keycloak ID
                    updated = kc_admin.update_onboarding_step(user.id, current_step)
                    user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)  # Use helper method to get email from cache
                    logger.info(f"[OnboardingProgress] Synced step '{current_step}' to Keycloak for {user_email}: updated={updated}")
                    
                    # Invalidate cache so next API call gets fresh data
                    from users.services import UserCacheService
                    UserCacheService.invalidate_user_cache(user.id)  # Single ID: id IS the Keycloak ID
                    
                else:
                    user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)  # Use helper method to get email from cache
                    logger.warning(f"[OnboardingProgress] No user ID for user {user_email}, cannot sync step")
            except Exception as e:
                # Best-effort; do not block step saving if Keycloak sync fails
                user_email = user.get_email()  # Use helper method to get email from cache
                logger.warning(f"[OnboardingProgress] Could not sync step to Keycloak for {user_email}: {e}")
            
            logger.info(f"Saved onboarding step '{step}' for user {user.id}. Next step is '{current_step}'.")
            
            return Response({
                'success': True,
                'step': step,
                'current_step': progress.current_step,
                'tenant_id': getattr(request.tenant, 'slug', 'spoton-energy'),
                'environment': getattr(request, 'environment', 'uat'),
                'autosave': autosave,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in onboarding progress POST: {str(e)}")
            return Response(
                {"error": "Failed to save onboarding progress"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OnboardingFinalizeView(APIView):
    authentication_classes = []  # Bypass DRF authentication
    permission_classes = []      # Allow any access, we'll handle auth manually

    def _parse_address_components(self, full_address: str):
        """
        Best-effort address parsing from a single line string.
        Returns dict with keys: address_line1, suburb, city, region, postal_code.
        Postal code may be missing in onboarding, so default to '0000' in UAT.
        """
        parts = [p.strip() for p in (full_address or '').split(',') if p.strip()]
        address_line1, suburb, city, region = '', '', '', ''
        postal_code = ''
        if len(parts) == 1:
            address_line1 = parts[0]
        elif len(parts) == 2:
            address_line1, city = parts
        elif len(parts) == 3:
            address_line1, suburb, city = parts
        elif len(parts) >= 4:
            address_line1, suburb, city, region = parts[:4]
        # Fallback postal code for UAT/testing when not provided
        postal_code = '0000'
        return {
            'address_line1': address_line1 or full_address or '',
            'suburb': suburb,
            'city': city or region or 'Auckland',
            'region': region,
            'postal_code': postal_code,
        }

    def _normalize_onboarding_data(self, progress: OnboardingProgress, request):
        """
        Normalize onboarding JSON from progress.step_data or request payload.
        """
        payload = request.data if isinstance(request.data, dict) else {}
        step_data = progress.step_data or {}
        # Prefer explicit payload keys if provided; otherwise fall back to step_data
        about_you = payload.get('aboutYou') or step_data.get('aboutYou') or {}
        your_services = payload.get('yourServices') or step_data.get('yourServices') or {}
        selected_services = your_services.get('selectedServices') or step_data.get('selectedServices') or {}
        selected_plans = your_services.get('selectedPlans') or step_data.get('selectedPlans') or {}
        selected_address = your_services.get('selectedAddress') or step_data.get('selectedAddress') or {}
        preferences = payload.get('preferences') or step_data.get('preferences') or {}
        how_you_pay = payload.get('howYoullPay') or step_data.get('howYoullPay') or {}
        service_details_wrapper = payload.get('serviceDetails') or step_data.get('serviceDetails') or {}
        service_details = service_details_wrapper.get('data', {}).get('serviceDetails') or service_details_wrapper.get('serviceDetails') or {}
        return {
            'about_you': about_you,
            'selected_services': selected_services,
            'selected_plans': selected_plans,
            'selected_address': selected_address,
            'preferences': preferences,
            'how_you_pay': how_you_pay,
            'service_details': service_details,
        }

    @transaction.atomic
    def post(self, request):
        # Use unified authentication service - works for ALL authentication methods
        from core.services.unified_auth_service import UnifiedAuthService
        
        auth_result = UnifiedAuthService.authenticate_user(request)
        if not auth_result.is_authenticated:
            return Response(
                {"error": "Authentication required", "details": auth_result.error},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = auth_result.user
        
        try:
            # Get onboarding progress
            try:
                progress = OnboardingProgress.objects.get(user=user)
            except OnboardingProgress.DoesNotExist:
                return Response(
                    {"error": "Onboarding progress not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Normalize onboarding data
            data = self._normalize_onboarding_data(progress, request)
            about_you = data['about_you']
            selected_services = data['selected_services']
            selected_plans = data['selected_plans']
            selected_address = data['selected_address']
            preferences = data['preferences']
            how_you_pay = data['how_you_pay']
            service_details = data['service_details']

            # Persist a structured snapshot for auditing/processing
            confirmation, _ = UserOnboardingConfirmation.objects.get_or_create(
                user=user,
                defaults={
                    'address_info': selected_address.get('yourServices') or selected_address,
                    'services_chosen': selected_services,
                    'plan_selections': selected_plans,
                    'personal_info': about_you,
                    'service_details': service_details,
                    'payment_info': {'paymentMethodType': how_you_pay.get('paymentMethodType')},
                    'notification_preferences': preferences.get('preferences') or {},
                    'is_completed': True,
                }
            )
            # Update if exists
            confirmation.address_info = selected_address.get('yourServices') or selected_address or {}
            confirmation.services_chosen = selected_services or {}
            confirmation.plan_selections = selected_plans or {}
            confirmation.personal_info = about_you or {}
            confirmation.service_details = service_details or {}
            confirmation.payment_info = {'paymentMethodType': how_you_pay.get('paymentMethodType')}
            confirmation.notification_preferences = preferences.get('preferences') or {}
            confirmation.is_completed = True
            confirmation.save()

            # Update core user identity in Keycloak (since identity fields removed from Django User model)
            try:
                from users.keycloak_admin import KeycloakAdminService
                from django.conf import settings
                
                # Use environment-specific realm
                environment = getattr(settings, 'ENVIRONMENT', 'uat')
                realm = f'spoton-{environment}'
                kc_admin = KeycloakAdminService(realm=realm)
                
                if user.id and about_you:  # Single ID: id IS the Keycloak ID
                    # Update user identity in Keycloak
                    update_data = {}
                    
                    if about_you.get('legalFirstName'):
                        update_data['firstName'] = about_you['legalFirstName']
                    if about_you.get('legalLastName'):
                        update_data['lastName'] = about_you['legalLastName']
                    if about_you.get('email'):
                        update_data['email'] = about_you['email']
                    
                    # Update attributes
                    attributes = {}
                    if about_you.get('mobile'):
                        attributes['mobile'] = about_you['mobile']  # Use normalized mobile field
                    
                    if update_data or attributes:
                        if attributes:
                            update_data['attributes'] = attributes
                        
                        updated = kc_admin.update_user(user.id, update_data)  # Single ID: id IS the Keycloak ID
                        user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)
                        logger.info(f"[OnboardingFinalize] Updated user identity in Keycloak for {user_email}: updated={updated}")
                        
                        # Invalidate cache to refresh identity data
                        from users.services import UserCacheService
                        UserCacheService.invalidate_user_cache(user.id)  # Single ID: id IS the Keycloak ID
                        
            except Exception as e:
                user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)
                logger.warning(f"[OnboardingFinalize] Could not update user identity in Keycloak for {user_email}: {e}")

            # Resolve tenant (primary brand)
            from users.models import Tenant, Account, Address, UserAccountRole
            tenant = Tenant.objects.filter(is_primary_brand=True).first()
            if not tenant:
                tenant = Tenant.objects.create(name='SpotOn Energy', slug='spoton', is_primary_brand=True)

            # Get or create account for user
            account = None
            existing_role = UserAccountRole.objects.filter(user=user, tenant=tenant).select_related('account').first()
            if existing_role:
                account = existing_role.account
            if not account:
                account = Account.objects.create(
                    tenant=tenant,
                    account_type='residential',
                    created_by=user,
                    billing_cycle='monthly',
                    billing_day=1,
                )
                UserAccountRole.objects.create(
                    tenant=tenant,
                    user=user,
                    account=account,
                    role='primary'
                )

            # Service address (from onboarding)
            full_addr = None
            if isinstance(selected_address, dict) and selected_address:
                full_addr = selected_address.get('full_address') or selected_address.get('yourServices', {}).get('full_address')
            if not full_addr:
                # Fallback: try in yourServices wrapper
                your_services_wrapper = progress.step_data.get('yourServices', {}) if progress.step_data else {}
                full_addr = your_services_wrapper.get('yourServices', {}).get('full_address') or your_services_wrapper.get('full_address')
            addr_components = self._parse_address_components(full_addr or '')
            service_address, _ = Address.objects.get_or_create(
                tenant=tenant,
                address_line1=addr_components['address_line1'],
                city=addr_components['city'],
                postal_code=addr_components['postal_code'],
                defaults={
                    'suburb': addr_components['suburb'],
                    'region': addr_components['region'],
                    'country': 'New Zealand',
                    'address_type': 'service',
                    'is_primary': True,
                }
            )

            # If no billing address, set same as service address for now
            if account.billing_address is None:
                account.billing_address = service_address
                account.save(update_fields=['billing_address'])

            # Create service contracts and connections for all selected services
            created_objects = {}
            
            # Import models
            from core.contracts.models import ServiceContract
            from energy.connections.models import Connection
            
            # CRITICAL FIX: Create actual Plan records from onboarding selections
            created_plan_ids = self._create_plans_from_selections(tenant, selected_plans)
            
            # Create broadband contract and connection if broadband selected
            if selected_services.get('broadband') or selected_services.get('hasBroadband'):
                logger.info(f"[OnboardingFinalize] Creating broadband service for user {user.id}")
                
                # Contract
                contract = ServiceContract.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_type='broadband',
                    service_name=(selected_plans.get('broadband') or {}).get('name') or 'Broadband Service',
                    description='Created from onboarding completion',
                    start_date=timezone.now(),
                    status='pending',
                    billing_frequency='monthly',
                    base_charge=(selected_plans.get('broadband') or {}).get('charges', {}).get('monthly_charge') or 0,
                    metadata={
                        'plan': selected_plans.get('broadband') or {},
                        'linked_plan_id': created_plan_ids.get('broadband'),
                        'transferType': service_details.get('bb_transferType') or 'New',
                        'routerPreference': service_details.get('bb_routerPreference') or 'BYO',
                        'serviceStartDate': service_details.get('bb_serviceStartDate') or 'asap',
                    },
                    created_by=user,
                    updated_by=user,
                )
                created_objects['broadband_contract_id'] = str(contract.id)

                # Connection
                plan = selected_plans.get('broadband') or {}
                line_speed = None
                dl, ul = plan.get('download_speed'), plan.get('upload_speed')
                if dl or ul:
                    line_speed = f"{(dl or '').replace(' Mbps','')}/{(ul or '').replace(' Mbps','')} Mbps".strip()
                connection = Connection.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_id=contract.id,
                    service_address=service_address,
                    service_type='broadband',
                    connection_identifier=f"BB-{account.account_number}",
                    status='pending',
                    line_speed=line_speed or '',
                )
                created_objects['broadband_connection_id'] = str(connection.id)
                logger.info(f"[OnboardingFinalize] Created broadband contract {contract.id} and connection {connection.id}")

            # Create mobile contract and connection if mobile selected
            if selected_services.get('mobile') or selected_services.get('hasMobile'):
                logger.info(f"[OnboardingFinalize] Creating mobile service for user {user.id}")
                
                # Contract
                mobile_plan = selected_plans.get('mobile') or {}
                contract = ServiceContract.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_type='mobile',
                    service_name=mobile_plan.get('name') or 'Mobile Service',
                    description='Created from onboarding completion',
                    start_date=timezone.now(),
                    status='pending',
                    billing_frequency='monthly',
                    base_charge=mobile_plan.get('charges', {}).get('monthly_charge') or mobile_plan.get('rate') or 0,
                    metadata={
                        'plan': mobile_plan,
                        'linked_plan_id': created_plan_ids.get('mobile'),
                        'plan_type': mobile_plan.get('plan_type') or 'postpaid',
                        'data_allowance': mobile_plan.get('charges', {}).get('data_allowance') or 'Unlimited',
                        'minutes': mobile_plan.get('charges', {}).get('minutes') or 'Unlimited',
                        'serviceStartDate': service_details.get('mobile_serviceStartDate') or 'asap',
                    },
                    created_by=user,
                    updated_by=user,
                )
                created_objects['mobile_contract_id'] = str(contract.id)

                # Connection (mobile doesn't need service_address)
                # Generate a placeholder mobile number for validation
                placeholder_mobile = f"+64-MOB-{account.account_number[-6:]}"
                
                connection = Connection.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_id=contract.id,
                    service_address=None,  # Mobile services don't have a physical address
                    service_type='mobile',
                    connection_identifier=placeholder_mobile,
                    mobile_number=placeholder_mobile,  # Required for validation
                    status='pending_activation',
                    metadata={
                        'plan_type': mobile_plan.get('plan_type') or 'postpaid',
                        'awaiting_sim_activation': True,
                        'placeholder_number': True,  # Flag to indicate this is a placeholder
                    }
                )
                created_objects['mobile_connection_id'] = str(connection.id)
                logger.info(f"[OnboardingFinalize] Created mobile contract {contract.id} and connection {connection.id}")

            # Create electricity contract and connection if electricity selected
            if selected_services.get('electricity') or selected_services.get('hasElectricity') or selected_services.get('power'):
                logger.info(f"[OnboardingFinalize] Creating electricity service for user {user.id}")
                
                # Contract
                electricity_plan = selected_plans.get('electricity') or {}
                # Calculate base charge from electricity plan structure
                base_charge = 0
                charges = electricity_plan.get('charges', {})
                if charges:
                    # Get standard charges (most common tier)
                    standard_charges = charges.get('standard', {})
                    daily_charge = standard_charges.get('daily_charge', {}).get('amount', 0)
                    # Estimate monthly base charge (daily charge * 30)
                    base_charge = float(daily_charge) * 30 if daily_charge else 0
                
                contract = ServiceContract.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_type='electricity',
                    service_name=electricity_plan.get('name') or 'Electricity Supply',
                    description='Created from onboarding completion',
                    start_date=timezone.now(),
                    status='pending',
                    billing_frequency='monthly',
                    base_charge=base_charge,
                    metadata={
                        'plan': electricity_plan,
                        'linked_plan_id': created_plan_ids.get('electricity'),
                        'charges': charges,
                        'plan_type': 'standard',
                        'serviceStartDate': service_details.get('power_serviceStartDate') or 'asap',
                    },
                    created_by=user,
                    updated_by=user,
                )
                created_objects['electricity_contract_id'] = str(contract.id)

                # Connection
                # Generate a placeholder ICP code for validation
                placeholder_icp = f"ICP-{account.account_number[-6:]}"
                
                connection = Connection.objects.create(
                    tenant=tenant,
                    account=account,
                    contract_id=contract.id,
                    service_address=service_address,
                    service_type='electricity',
                    connection_identifier=placeholder_icp,
                    icp_code=placeholder_icp,  # Required for validation
                    status='pending_switch',
                    metadata={
                        'awaiting_retailer_switch': True,
                        'estimated_switch_days': '2-3 business days',
                        'placeholder_icp': True,  # Flag to indicate this is a placeholder
                    }
                )
                created_objects['electricity_connection_id'] = str(connection.id)
                logger.info(f"[OnboardingFinalize] Created electricity contract {contract.id} and connection {connection.id}")

            # Save user notification preferences
            from core.user_details.models import UserPreferences as PrefModel
            pref_model, _ = PrefModel.objects.get_or_create(user=user)
            pref_model.notification_preferences = preferences.get('preferences') or {}
            pref_model.communication_preferences = {}
            pref_model.save()

            # Mark onboarding as completed in both Django and Keycloak
            progress.is_completed = True
            progress.current_step = 'completed'
            progress.save()
            
            # Update Keycloak with onboarding completion
            try:
                from users.keycloak_admin import KeycloakAdminService
                from django.conf import settings
                
                # Use environment-specific realm
                environment = getattr(settings, 'ENVIRONMENT', 'uat')
                realm = f'spoton-{environment}'
                kc_admin = KeycloakAdminService(realm=realm)
                
                if user.id:  # Single ID: id IS the Keycloak ID
                    updated = kc_admin.set_onboarding_complete(user.id, complete=True, step='completed')
                    user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)
                    logger.info(f"[OnboardingFinalize] Set onboarding complete in Keycloak for {user_email}: updated={updated}")
                    
                    # Invalidate cache so next API call gets fresh data
                    from users.services import UserCacheService
                    UserCacheService.invalidate_user_cache(user.id)  # Single ID: id IS the Keycloak ID
                    logger.info(f"[OnboardingFinalize] Invalidated cache for {user_email}")
                    
                else:
                    user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)
                    logger.warning(f"[OnboardingFinalize] No user ID for user {user_email}, cannot sync onboarding status")
            except Exception as e:
                # Best-effort; do not block finalization if Keycloak sync fails
                user_email = user.get_email() if hasattr(user, 'get_email') else str(user.id)
                logger.warning(f"[OnboardingFinalize] Could not sync onboarding completion to Keycloak for {user_email}: {e}")
            
            logger.info(f"Finalized onboarding for user {user.id}")
            
            # Get fresh user data to return to frontend
            # Bypass cache service since it's failing - use data from JWT/request context
            fresh_user_data = {}
            try:
                # Try to get cached data first
                fresh_user_data = user.get_cached_data() or {}
            except Exception as cache_error:
                logger.warning(f"[OnboardingFinalize] Cache service failed for user {user.id}: {cache_error}")
                # Use fallback data from request context or basic user info
                fresh_user_data = {
                    'email': getattr(user, 'email', ''),
                    'first_name': '',
                    'last_name': '',
                    'mobile': '',
                    'mobile_verified': True,  # Assume verified since they completed onboarding
                    'email_verified': True,  # Assume verified since they completed onboarding
                }
            
            # Build updated user data with onboarding completion
            updated_user_data = {
                'id': str(user.id),
                'email': fresh_user_data.get('email', ''),
                'first_name': fresh_user_data.get('first_name', ''),
                'last_name': fresh_user_data.get('last_name', ''),
                'mobile': fresh_user_data.get('mobile', ''),
                'mobile_verified': fresh_user_data.get('mobile_verified', False),
                'email_verified': fresh_user_data.get('email_verified', False),
                'is_onboarding_complete': True,  # Always True after successful finalization
                'keycloak_id': user.id  # Single ID: id IS the Keycloak ID
            }
            
            response = Response({
                'success': True,
                'message': 'Onboarding finalized and data persisted',
                'user_id': str(user.id),
                'account_id': str(account.id),
                'service_address_id': str(service_address.id),
                **created_objects,
                'tenant_id': getattr(request.tenant, 'slug', 'spoton-energy'),
                'environment': getattr(request, 'environment', 'uat'),
                'finalized_at': timezone.now().isoformat(),
                'user': updated_user_data,
                # Signal to frontend that authentication state has been updated
                'auth_updated': True
            })
            
            # CRITICAL FIX: Maintain authentication cookies with updated state
            # Instead of clearing cookies (which caused the logout issue), 
            # refresh the authentication with the updated onboarding status
            access_token = request.COOKIES.get('access_token')
            if access_token:
                # Use unified service to maintain authentication consistency
                UnifiedAuthService.set_authentication(
                    response=response,
                    user_data=updated_user_data,
                    auth_method=auth_result.auth_method,
                    access_token=access_token
                )
                logger.info(f"[OnboardingFinalize] Maintained authentication for {auth_result.auth_method} user")
            else:
                logger.warning(f"[OnboardingFinalize] No access token found - authentication may be lost")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in onboarding finalize: {str(e)}")
            logger.debug(traceback.format_exc())
            return Response(
                {"error": "Failed to finalize onboarding"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _create_plans_from_selections(self, tenant, selected_plans):
        """
        Create actual Plan records from onboarding selections
        CRITICAL FIX: This ensures plans show up in staff portal
        """
        from decimal import Decimal
        created_plan_ids = {}
        
        logger.info(f"[OnboardingFinalize] Creating plan records for tenant {tenant.id}")
        
        for service_type, plan_data in selected_plans.items():
            if not plan_data or not isinstance(plan_data, dict):
                continue
                
            try:
                plan_id = None
                
                if service_type == 'electricity':
                    plan_id = self._create_electricity_plan(tenant, plan_data)
                elif service_type == 'broadband':
                    plan_id = self._create_broadband_plan(tenant, plan_data)
                elif service_type == 'mobile':
                    plan_id = self._create_mobile_plan(tenant, plan_data)
                
                if plan_id:
                    created_plan_ids[service_type] = plan_id
                    # Also create ServicePlan for unified access
                    self._create_service_plan(tenant, service_type, plan_data)
                    
            except Exception as e:
                logger.error(f"[OnboardingFinalize] Error creating {service_type} plan: {e}")
        
        logger.info(f"[OnboardingFinalize] Created {len(created_plan_ids)} plan records")
        return created_plan_ids

    def _create_electricity_plan(self, tenant, plan_data):
        """Create ElectricityPlan record"""
        try:
            from web_support.public_pricing.models import ElectricityPlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"ELEC-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            existing = ElectricityPlan.objects.filter(tenant=tenant, plan_id=plan_id).first()
            if existing:
                return plan_id
            
            charges = plan_data.get('charges', {})
            
            plan = ElectricityPlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Electricity Plan'),
                plan_type=plan_data.get('type', 'fixed'),
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/electricity',
                city=plan_data.get('city', 'Auckland'),
                base_rate=Decimal(str(charges.get('unit_rate', 0.25))),
                rate_details=f"Unit rate: {charges.get('unit_rate', 0.25)}c/kWh",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 0))),
                standard_daily_charge=Decimal(str(charges.get('daily_charge', 1.50))),
                standard_variable_charge=Decimal(str(charges.get('unit_rate', 0.25))),
                low_user_daily_charge=Decimal(str(charges.get('daily_charge', 1.50))),
                low_user_variable_charge=Decimal(str(charges.get('unit_rate', 0.25))),
                valid_from=timezone.now()
            )
            
            logger.info(f"[OnboardingFinalize] Created electricity plan: {plan.name}")
            return plan_id
            
        except Exception as e:
            logger.error(f"[OnboardingFinalize] Error creating electricity plan: {e}")
            return None

    def _create_broadband_plan(self, tenant, plan_data):
        """Create BroadbandPlan record"""
        try:
            from web_support.public_pricing.models import BroadbandPlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"BB-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            existing = BroadbandPlan.objects.filter(tenant=tenant, plan_id=plan_id).first()
            if existing:
                return plan_id
            
            charges = plan_data.get('charges', {})
            
            plan = BroadbandPlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Broadband Plan'),
                plan_type='fibre',
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/broadband',
                city=plan_data.get('city', 'Auckland'),
                base_rate=Decimal(str(charges.get('monthly_charge', 79.99))),
                rate_details=f"Monthly: ${charges.get('monthly_charge', 79.99)}",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 79.99))),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                data_allowance=plan_data.get('data_allowance', 'Unlimited'),
                download_speed=plan_data.get('download_speed', '100 Mbps'),
                upload_speed=plan_data.get('upload_speed', '20 Mbps'),
                valid_from=timezone.now()
            )
            
            logger.info(f"[OnboardingFinalize] Created broadband plan: {plan.name}")
            return plan_id
            
        except Exception as e:
            logger.error(f"[OnboardingFinalize] Error creating broadband plan: {e}")
            return None

    def _create_mobile_plan(self, tenant, plan_data):
        """Create MobilePlan record"""
        try:
            from web_support.public_pricing.models import MobilePlan
            
            plan_id = plan_data.get('pricing_id') or plan_data.get('plan_id') or f"MOB-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if plan already exists
            existing = MobilePlan.objects.filter(tenant=tenant, plan_id=plan_id).first()
            if existing:
                return plan_id
            
            charges = plan_data.get('charges', {})
            
            plan = MobilePlan.objects.create(
                tenant=tenant,
                plan_id=plan_id,
                name=plan_data.get('name', 'Mobile Plan'),
                plan_type='postpaid',
                description=plan_data.get('description', 'Plan created from onboarding'),
                term='12_month',
                terms_url='https://spoton.co.nz/terms/mobile',
                city='nz',
                base_rate=Decimal(str(charges.get('monthly_charge', 49.99))),
                rate_details=f"Monthly: ${charges.get('monthly_charge', 49.99)}",
                monthly_charge=Decimal(str(charges.get('monthly_charge', 49.99))),
                data_allowance=plan_data.get('data_allowance', '20GB'),
                minutes=plan_data.get('minutes', 'Unlimited'),
                texts=plan_data.get('texts', 'Unlimited'),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                sim_card_fee=Decimal('5.00'),
                valid_from=timezone.now()
            )
            
            logger.info(f"[OnboardingFinalize] Created mobile plan: {plan.name}")
            return plan_id
            
        except Exception as e:
            logger.error(f"[OnboardingFinalize] Error creating mobile plan: {e}")
            return None

    def _create_service_plan(self, tenant, service_type, plan_data):
        """Create ServicePlan for unified access"""
        try:
            from finance.pricing.models import ServicePlan
            
            plan_code = f"{service_type.upper()}-{plan_data.get('pricing_id', plan_data.get('plan_id', timezone.now().strftime('%Y%m%d%H%M%S')))}"
            
            # Check if plan already exists
            existing = ServicePlan.objects.filter(tenant=tenant, plan_code=plan_code).first()
            if existing:
                return
            
            charges = plan_data.get('charges', {})
            
            ServicePlan.objects.create(
                tenant=tenant,
                plan_code=plan_code,
                plan_name=plan_data.get('name', f'{service_type.title()} Plan'),
                service_type=service_type,
                plan_type='fixed',
                description=plan_data.get('description', f'Plan created from onboarding for {service_type}'),
                base_price=Decimal(str(charges.get('unit_rate', charges.get('monthly_charge', 0)))),
                monthly_fee=Decimal(str(charges.get('monthly_charge', 0))),
                setup_fee=Decimal(str(charges.get('setup_fee', 0))),
                status='active',
                available_from=timezone.now(),
                service_config=plan_data
            )
            
            logger.info(f"[OnboardingFinalize] Created service plan: {plan_code}")
            
        except Exception as e:
            logger.error(f"[OnboardingFinalize] Error creating service plan: {e}")

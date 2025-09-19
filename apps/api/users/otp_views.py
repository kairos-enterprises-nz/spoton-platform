from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .otp_service import OTPService
from .keycloak_admin import KeycloakAdminService
from django.contrib.auth import get_user_model
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()

class OTPSendView(APIView):
    """
    API endpoint for sending OTP
    """
    authentication_classes = []  # Bypass all authentication for public endpoint
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Send OTP to phone or email
        
        Request body:
        {
            "type": "mobile" | "email",
            "identifier": "phone_number" | "email_address",
            "purpose": "signup" | "login" | "reset"
        }
        """
        type = request.data.get('type')
        identifier = request.data.get('identifier')
        purpose = request.data.get('purpose', 'verification')
        
        if not type or not identifier:
            return Response({
                'error': 'Type and identifier are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if type not in ['mobile', 'email']:
            return Response({
                'error': 'Type must be mobile or email'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        result = OTPService.send_otp(type, identifier, purpose)
        
        if result['success']:
            return Response({
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(APIView):
    """
    API endpoint for verifying OTP
    """
    authentication_classes = []  # Bypass all authentication for public endpoint
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Verify OTP
        
        Request body:
        {
            "type": "mobile" | "email",
            "identifier": "phone_number" | "email_address",
            "otp": "123456",
            "purpose": "signup" | "login" | "reset"
        }
        """
        type = request.data.get('type')
        identifier = request.data.get('identifier')
        otp = request.data.get('otp')
        purpose = request.data.get('purpose', 'verification')
        
        if not type or not identifier or not otp:
            return Response({
                'error': 'Type, identifier, and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if type not in ['mobile', 'email']:
            return Response({
                'error': 'Type must be mobile or email'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        result = OTPService.verify_otp(type, identifier, otp, purpose)
        
        if result['success']:
            # Update user verification status if applicable
            if purpose == 'signup' or purpose == 'verification' or purpose == 'phone_verification':
                self._update_verification_status(type, identifier, request)
                
            return Response({
                'message': result['message'],
                'verified': True
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['message'],
                'verified': False
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _update_verification_status(self, type, identifier, request=None):
        """Update verification status in Django and Keycloak"""
        try:
            if type == 'mobile' and request:
                # For phone verification, try to find user from cookies (for authenticated users)
                access_token = request.COOKIES.get('access_token')
                if access_token:
                    try:
                        # Import here to avoid circular imports
                        from web_support.onboarding.views import get_user_from_keycloak_token
                        
                        # Get user from token (handles both auto-login and real Keycloak tokens)
                        user = get_user_from_keycloak_token(request)
                        if user:
                            # Update user's phone verification status
                            user.phone = identifier
                            user.phone_verified = True
                            user.save(update_fields=['phone', 'phone_verified'])
                            
                            logger.info(f"[OTP] Phone verification completed for user {user.email}: {identifier}")
                            return
                            
                    except Exception as e:
                        logger.error(f"[OTP] Error getting user from token: {e}")
                
                # Fallback: try to find user by phone number
                try:
                    User = get_user_model()
                    user = User.objects.filter(phone=identifier).first()
                    if user:
                        user.phone_verified = True
                        user.save(update_fields=['phone_verified'])
                        logger.info(f"[OTP] Phone verification completed for user {user.email}: {identifier}")
                    else:
                        logger.warning(f"[OTP] No user found with phone {identifier}")
                        
                except Exception as e:
                    logger.error(f"[OTP] Error finding user by phone: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to update verification status: {e}")
            # Don't fail the request if this fails 
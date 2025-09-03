from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .otp_service import OTPService
from django.contrib.auth import get_user_model
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class PhoneVerificationSendView(APIView):
    """
    Send OTP for phone verification (supports both authenticated users and OAuth callback flow)
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access for OAuth flow
    
    def post(self, request):
        """
        Send OTP to user's phone for verification
        
        Request body:
        {
            "phone": "phone_number",
            "email": "user_email" (optional, for OAuth flow identification)
        }
        """
        phone = request.data.get('phone')
        email = request.data.get('email')
        
        if not phone:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to get user from authentication first
        user = None
        if request.user and request.user.is_authenticated:
            user = request.user
        elif email:
            # For OAuth callback flow, find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found. Please complete the registration process first.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Authentication required or email must be provided'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Update user's phone number
        user.phone = phone
        user.save()
        
        logger.info(f"[PhoneVerification] Sending OTP to {phone} for user {user.email}")
        
        # Send OTP
        result = OTPService.send_otp('mobile', phone, 'phone_verification')
        
        if result['success']:
            return Response({
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerificationVerifyView(APIView):
    """
    Verify OTP and update user's phone verification status (supports both authenticated users and OAuth callback flow)
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access for OAuth flow
    
    def post(self, request):
        """
        Verify OTP and mark phone as verified
        
        Request body:
        {
            "phone": "phone_number",
            "otp": "123456",
            "email": "user_email" (optional, for OAuth flow identification)
        }
        """
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        email = request.data.get('email')
        
        if not phone or not otp:
            return Response({
                'error': 'Phone number and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to get user from authentication first
        user = None
        if request.user and request.user.is_authenticated:
            user = request.user
        elif email:
            # For OAuth callback flow, find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found. Please complete the registration process first.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'Authentication required or email must be provided'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Verify OTP
        result = OTPService.verify_otp('mobile', phone, otp, 'phone_verification')
        
        if result['success']:
            # Update user's phone verification status
            user.phone = phone
            user.phone_verified = True
            user.save()
            
            logger.info(f"[PhoneVerification] Phone verified for user {user.email}: {phone}")
            
            # Check onboarding completion status using only is_completed
            is_onboarding_complete = False
            try:
                from users.models import OnboardingProgress
                onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
                is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
                logger.info(f"[PhoneVerification] Onboarding status for {user.email}: {is_onboarding_complete}")
            except Exception as e:
                logger.error(f"[PhoneVerification] Error checking onboarding status for {user.email}: {e}")
                is_onboarding_complete = False

            # Use unified social auth framework for consistent experience
            try:
                from core.social_auth_framework import SocialAuthFramework
                # Determine post-authentication flow using framework
                flow_info = SocialAuthFramework.determine_post_auth_flow(user, is_social_login=True)
            except ImportError:
                # Fallback if social auth framework is not available
                flow_info = {
                    'next_step': 'onboarding' if not is_onboarding_complete else 'dashboard',
                    'login_url': None
                }

            return Response({
                'success': True,
                'message': 'Phone number verified successfully',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'phone_verified': user.phone_verified,
                    'email_verified': user.email_verified,
                    'is_onboarding_complete': is_onboarding_complete,
                    'is_staff': user.is_staff
                },
                'redirect': flow_info
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
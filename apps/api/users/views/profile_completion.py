import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from ..services.verification import send_otp, verify_otp
from users.models import OnboardingProgress

logger = logging.getLogger(__name__)
User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class ProfileCompletionView(View):
    """
    Handle profile completion for social login users
    """
    
    def get(self, request):
        """Get user's profile completion status"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user = request.user
            
            # Check what fields are missing
            missing_fields = []
            completion_status = {
                'is_complete': True,
                'missing_fields': [],
                'user_info': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'mobile': user.mobile,
                    'email_verified': user.email_verified,
                    'phone_verified': user.phone_verified,
                    'registration_method': user.registration_method,
                    'social_provider': user.social_provider,
                }
            }
            
            # For social login users, check if mobile is missing or unverified
            if user.registration_method == 'social':
                if not user.mobile:
                    missing_fields.append('mobile')
                    completion_status['is_complete'] = False
                elif not user.phone_verified:
                    missing_fields.append('mobile_verification')
                    completion_status['is_complete'] = False
            
            completion_status['missing_fields'] = missing_fields
            
            return JsonResponse(completion_status)
            
        except Exception as e:
            logger.error(f"Error getting profile completion status: {e}")
            return JsonResponse({'error': 'Failed to get profile status'}, status=500)
    
    def post(self, request):
        """Update user profile with missing information"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user = request.user
            data = json.loads(request.body)
            
            # Update mobile number if provided
            mobile = data.get('mobile')
            if mobile:
                # Validate mobile format (NZ format)
                import re
                mobile_pattern = r'^(02|021|022|027|028|029)\d{7,8}$'
                if not re.match(mobile_pattern, mobile):
                    return JsonResponse({'error': 'Invalid mobile number format'}, status=400)
                
                user.mobile = mobile
                user.phone_verified = False  # Will need to verify the new number
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Mobile number updated. Please verify it.',
                    'requires_verification': True
                })
            
            return JsonResponse({'error': 'No valid data provided'}, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return JsonResponse({'error': 'Failed to update profile'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MobileVerificationView(View):
    """
    Handle mobile verification for profile completion
    """
    
    def post(self, request):
        """Send or verify mobile OTP"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            user = request.user
            data = json.loads(request.body)
            action = data.get('action')  # 'send' or 'verify'
            
            if not user.mobile:
                return JsonResponse({'error': 'Mobile number not set'}, status=400)
            
            if action == 'send':
                # Send OTP to user's mobile
                result = send_otp('mobile', user.mobile)
                if result.get('success'):
                    return JsonResponse({
                        'success': True,
                        'message': 'OTP sent to your mobile number'
                    })
                else:
                    return JsonResponse({
                        'error': result.get('message', 'Failed to send OTP')
                    }, status=500)
            
            elif action == 'verify':
                # Verify OTP
                otp_code = data.get('otp')
                if not otp_code:
                    return JsonResponse({'error': 'OTP code required'}, status=400)
                
                result = verify_otp('mobile', user.mobile, otp_code)
                if result.get('success'):
                    # Mark phone as verified
                    user.phone_verified = True
                    user.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Mobile number verified successfully',
                        'profile_complete': True
                    })
                else:
                    return JsonResponse({
                        'error': result.get('message', 'Invalid OTP code')
                    }, status=400)
            
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Error in mobile verification: {e}")
            return JsonResponse({'error': 'Verification failed'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_profile_completion(request):
    """
    API endpoint to check if user's profile is complete
    """
    user = request.user
    
    # Check if profile completion is required
    needs_completion = False
    required_actions = []
    
    if user.registration_method == 'social':
        if not user.mobile:
            needs_completion = True
            required_actions.append('add_mobile')
        elif not user.phone_verified:
            needs_completion = True
            required_actions.append('verify_mobile')
    
    # Check onboarding completion status from the proper table
    is_onboarding_complete = False
    try:
        onboarding_progress = OnboardingProgress.objects.filter(user=user).first()
        is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
    except Exception:
        # Default to false if we can't check
        is_onboarding_complete = False

    return Response({
        'needs_completion': needs_completion,
        'required_actions': required_actions,
        'user_info': {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'mobile': user.mobile,
            'email_verified': getattr(user, 'email_verified', user.is_email_verified),
            'phone_verified': getattr(user, 'phone_verified', user.is_mobile_verified),
            'registration_method': getattr(user, 'registration_method', 'custom'),
            'social_provider': getattr(user, 'social_provider', None),
            'is_onboarding_complete': is_onboarding_complete,
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_social_profile(request):
    """
    Complete profile for social login users
    """
    user = request.user
    data = request.data
    
    try:
        # Add mobile number
        mobile = data.get('mobile')
        if mobile:
            # Validate mobile format
            import re
            mobile_pattern = r'^(02|021|022|027|028|029)\d{7,8}$'
            if not re.match(mobile_pattern, mobile):
                return Response(
                    {'error': 'Invalid mobile number format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.mobile = mobile
            user.phone_verified = False  # Will need verification
            user.save()
            
            return Response({
                'success': True,
                'message': 'Mobile number added. Please verify it to complete your profile.',
                'next_step': 'verify_mobile'
            })
        
        return Response(
            {'error': 'Mobile number is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except Exception as e:
        logger.error(f"Error completing social profile: {e}")
        return Response(
            {'error': 'Failed to update profile'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 
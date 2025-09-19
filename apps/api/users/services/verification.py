"""
Verification services for OTP handling
"""
import logging
import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from ..utils import generate_otp_code
from ..models import OTP

logger = logging.getLogger(__name__)

def send_otp(method, identifier, purpose='signup'):
    """
    Send OTP via email or SMS
    
    Args:
        method: 'email' or 'mobile'
        identifier: email address or phone number
        purpose: purpose of OTP (default: 'signup')
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    code = generate_otp_code()
    expires_at = timezone.now() + datetime.timedelta(minutes=settings.OTP_EXPIRATION_TIME)

    # Delete previous OTPs for this identifier and purpose to avoid conflicts
    OTP.objects.filter(identifier=identifier, purpose=purpose).delete()
    OTP.objects.create(identifier=identifier, code=code, expires_at=expires_at, purpose=purpose)

    try:
        if method == "email":
            send_mail(
                f"Your OTP for {purpose.replace('_', ' ').title()}",
                f"Your One-Time Password (OTP) is: {code}",
                settings.DEFAULT_FROM_EMAIL,
                [identifier],
            )
            logger.info(f"[OTP] Email sent to {identifier} for {purpose}: Code {code}")
        else:  # mobile
            # Replace with actual SMS sending logic
            logger.info(f"[OTP] SMS to {identifier} for {purpose}: Code {code} (SMS sending not implemented)")
            print(f"[OTP] SMS to {identifier} for {purpose}: {code}")
        
        return {'success': True, 'message': f"OTP sent to your {method}."}
    except Exception as e:
        logger.error(f"[OTP] Failed to send OTP to {identifier} for {purpose}: {e}")
        return {'success': False, 'message': "Failed to send OTP. Please try again later."}

def verify_otp(identifier, otp, purpose='signup'):
    """
    Verify OTP code
    
    Args:
        identifier: email address or phone number
        otp: OTP code to verify
        purpose: purpose of OTP (default: 'signup')
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not otp:
        return {'success': False, 'message': "OTP code is required."}

    logger.info(f"[OTP] Verifying OTP for {identifier} ({purpose}): Submitted OTP {otp}")
    try:
        entry = OTP.objects.get(
            identifier=identifier,
            code=otp,
            purpose=purpose,
            is_used=False
        )
        
        if entry.expires_at < timezone.now():
            return {'success': False, 'message': "OTP has expired. Please request a new one."}
        
        # Mark as used
        entry.is_used = True
        entry.save()
        
        logger.info(f"[OTP] OTP verified successfully for {identifier} ({purpose})")
        return {'success': True, 'message': "OTP verified successfully."}
        
    except OTP.DoesNotExist:
        logger.warning(f"[OTP] Invalid OTP for {identifier} ({purpose}): {otp}")
        return {'success': False, 'message': "Invalid OTP code."}
    except Exception as e:
        logger.error(f"[OTP] Error verifying OTP for {identifier} ({purpose}): {e}")
        return {'success': False, 'message': "Error verifying OTP. Please try again."} 
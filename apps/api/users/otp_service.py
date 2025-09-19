import logging
import random
import hashlib
import time
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class OTPService:
    """
    Service for generating, sending, and verifying OTPs for phone and email verification.
    
    Features:
    - Rate limiting
    - Brute-force protection
    - Expiry (configurable TTL)
    - Hashed OTP storage
    - Audit logging
    """
    
    # OTP configuration
    OTP_LENGTH = 6
    OTP_TTL_SECONDS = 300  # 5 minutes
    RESEND_COOLDOWN_SECONDS = 60  # 1 minute
    MAX_ATTEMPTS = 3
    
    # Cache keys
    OTP_KEY_PREFIX = "otp:"
    ATTEMPT_KEY_PREFIX = "otp_attempt:"
    COOLDOWN_KEY_PREFIX = "otp_cooldown:"
    
    @classmethod
    def _get_otp_key(cls, type, identifier, purpose):
        """Get cache key for OTP"""
        return f"{cls.OTP_KEY_PREFIX}{type}:{identifier}:{purpose}"
    
    @classmethod
    def _get_attempt_key(cls, type, identifier, purpose):
        """Get cache key for attempts"""
        return f"{cls.ATTEMPT_KEY_PREFIX}{type}:{identifier}:{purpose}"
    
    @classmethod
    def _get_cooldown_key(cls, type, identifier, purpose):
        """Get cache key for cooldown"""
        return f"{cls.COOLDOWN_KEY_PREFIX}{type}:{identifier}:{purpose}"
    
    @classmethod
    def _hash_otp(cls, otp, identifier):
        """Hash OTP with identifier as salt"""
        return hashlib.sha256(f"{otp}:{identifier}".encode()).hexdigest()
    
    @classmethod
    def generate_otp(cls):
        """Generate a random OTP"""
        return str(random.randint(10**(cls.OTP_LENGTH-1), 10**cls.OTP_LENGTH - 1))
    
    @classmethod
    def send_otp(cls, type, identifier, purpose):
        """
        Generate and send OTP
        
        Args:
            type (str): 'mobile' or 'email'
            identifier (str): Phone number or email
            purpose (str): Purpose of OTP (e.g., 'signup', 'login', 'reset')
            
        Returns:
            dict: Result with success status and message
        """
        # Check cooldown
        cooldown_key = cls._get_cooldown_key(type, identifier, purpose)
        if cache.get(cooldown_key):
            cooldown_remaining = cache.ttl(cooldown_key)
            return {
                "success": False,
                "message": f"Please wait {cooldown_remaining} seconds before requesting another OTP"
            }
        
        # Generate OTP
        otp = cls.generate_otp()
        otp_hash = cls._hash_otp(otp, identifier)
        
        # Store hashed OTP in cache
        otp_key = cls._get_otp_key(type, identifier, purpose)
        cache.set(otp_key, otp_hash, cls.OTP_TTL_SECONDS)
        
        # Reset attempts
        attempt_key = cls._get_attempt_key(type, identifier, purpose)
        cache.set(attempt_key, 0, cls.OTP_TTL_SECONDS)
        
        # Set cooldown
        cache.set(cooldown_key, True, cls.RESEND_COOLDOWN_SECONDS)
        
        # Send OTP
        if type == 'mobile':
            cls._send_sms_otp(identifier, otp, purpose)
        elif type == 'email':
            cls._send_email_otp(identifier, otp, purpose)
        
        # Log (without OTP)
        logger.info(f"OTP sent to {type}:{identifier} for {purpose}")
        
        return {
            "success": True,
            "message": f"OTP sent to {type}"
        }
    
    @classmethod
    def verify_otp(cls, type, identifier, otp, purpose):
        """
        Verify OTP
        
        Args:
            type (str): 'mobile' or 'email'
            identifier (str): Phone number or email
            otp (str): OTP to verify
            purpose (str): Purpose of OTP
            
        Returns:
            dict: Result with success status and message
        """
        # Get keys
        otp_key = cls._get_otp_key(type, identifier, purpose)
        attempt_key = cls._get_attempt_key(type, identifier, purpose)
        
        # Check if OTP exists
        stored_hash = cache.get(otp_key)
        if not stored_hash:
            return {
                "success": False,
                "message": "OTP expired or not found"
            }
        
        # Check attempts
        attempts = cache.get(attempt_key, 0)
        if attempts >= cls.MAX_ATTEMPTS:
            # Clear OTP to prevent further attempts
            cache.delete(otp_key)
            cache.delete(attempt_key)
            return {
                "success": False,
                "message": f"Maximum attempts ({cls.MAX_ATTEMPTS}) exceeded"
            }
        
        # Increment attempts
        cache.set(attempt_key, attempts + 1, cls.OTP_TTL_SECONDS)
        
        # Verify OTP
        input_hash = cls._hash_otp(otp, identifier)
        if input_hash != stored_hash:
            return {
                "success": False,
                "message": "Invalid OTP"
            }
        
        # Clear OTP and attempts after successful verification
        cache.delete(otp_key)
        cache.delete(attempt_key)
        
        # Log success
        logger.info(f"OTP verified for {type}:{identifier} for {purpose}")
        
        return {
            "success": True,
            "message": f"{type.capitalize()} verified successfully"
        }
    
    @classmethod
    def _send_sms_otp(cls, phone, otp, purpose):
        """Send OTP via SMS"""
        # In production, integrate with SMS provider (Twilio, AWS SNS, etc.)
        if settings.DEBUG:
            logger.info(f"[DEBUG] SMS OTP: {otp} to {phone} for {purpose}")
        else:
            # Example: Twilio integration
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=f"Your verification code is: {otp}",
            #     from_=settings.TWILIO_PHONE_NUMBER,
            #     to=phone
            # )
            pass
    
    @classmethod
    def _send_email_otp(cls, email, otp, purpose):
        """Send OTP via email"""
        # In production, use Django's email system
        if settings.DEBUG:
            logger.info(f"[DEBUG] Email OTP: {otp} to {email} for {purpose}")
        else:
            from django.core.mail import send_mail
            subject = "Your Verification Code"
            message = f"Your verification code is: {otp}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email]) 
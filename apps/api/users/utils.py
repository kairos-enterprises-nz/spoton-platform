import random
import string
from django.conf import settings
from django.middleware.csrf import get_token
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def generate_otp_code(length=6, alphanumeric=False):
    """
    Generates a random OTP of the specified length.
    By default, it's digits only. Set alphanumeric=True for letters and digits.
    """
    if alphanumeric:
        characters = string.ascii_letters + string.digits
    else:
        characters = string.digits # Current implementation: digits only
    otp = ''.join(random.choice(characters) for _ in range(length))
    return otp

if __name__ == '__main__':
    print(f"Generated Numeric OTP: {generate_otp_code()}")
    print(f"Generated Alphanumeric OTP: {generate_otp_code(alphanumeric=True)}")


# ✅ REMOVED LEGACY JWT COOKIE FUNCTIONS
# Keycloak handles all authentication cookie management
# Django only manages user sync, not authentication cookies
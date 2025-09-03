"""
Django settings for UAT environment - Clean version.
"""

import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Environment identifier
ENVIRONMENT = 'uat'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'spoton_uat'),
        'USER': os.environ.get('DB_USER', 'spoton_uat_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'spoton_uat_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
        },
    }
}

# Allowed hosts for UAT
ALLOWED_HOSTS = [
    'uat.api.spoton.co.nz',
    'uat.spoton.co.nz', 
    'uat.portal.spoton.co.nz',
    'uat.staff.spoton.co.nz',
    'localhost',
    '127.0.0.1',
    'spoton-uat-api',
    'spoton-uat-api-local',
]

# CORS CONFIGURATION - Should inherit from main settings.py now
# Main settings.py now has CORS_ALLOW_ALL_ORIGINS = False

# Keycloak settings for UAT
KEYCLOAK_CONFIG = {
    'SERVER_URL': os.environ.get('KEYCLOAK_SERVER_URL', 'https://auth.kairosenterprises.co.nz'),
    'REALM': os.environ.get('KEYCLOAK_REALM', 'master'),
    'CLIENT_ID': os.environ.get('KEYCLOAK_CLIENT_ID', 'spoton-uat'),
    'CLIENT_SECRET': os.environ.get('KEYCLOAK_CLIENT_SECRET'),
}

print("🔧 Django settings loaded for UAT environment")
print(f"📊 Database: {DATABASES['default']['NAME']} on {DATABASES['default']['HOST']}")
print(f"🔐 Keycloak Realm: {KEYCLOAK_CONFIG['REALM']}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")

# EXPLICIT CORS ALLOWED ORIGINS FOR UAT
CORS_ALLOWED_ORIGINS = [
    "https://uat.spoton.co.nz",
    "https://uat.portal.spoton.co.nz", 
    "https://uat.staff.spoton.co.nz",
    "http://localhost:3000",
    "https://localhost:3000",
]

print("🔧 EXPLICIT CORS ORIGINS SET FOR UAT")
print(f"📋 CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")

# FIX LOGGING CONFIGURATION FOR CONTAINER
import logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

print("🔧 LOGGING CONFIGURATION FIXED FOR CONTAINER")

"""
Django settings for UAT environment.
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
        'HOST': os.environ.get('DB_HOST', 'spoton-uat-db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Allowed hosts for UAT environment
ALLOWED_HOSTS = [
    'uat.api.spoton.co.nz',
    'uat.spoton.co.nz',
    'uat.portal.spoton.co.nz',
    'uat.staff.spoton.co.nz',
    'localhost',
    '127.0.0.1',
    'spoton-uat-api',
]

# CORS settings for UAT
# Read from environment variable first, fallback to UAT defaults
CORS_ORIGINS_ENV = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if CORS_ORIGINS_ENV:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_ENV.split(',')]
else:
    # Default UAT CORS origins if environment variable not set
    CORS_ALLOWED_ORIGINS = [
        "https://uat.spoton.co.nz",
        "https://uat.portal.spoton.co.nz",
        "https://uat.staff.spoton.co.nz",
        "http://localhost:3000",
        "https://localhost:3000",
        "http://127.0.0.1:3000",
        "https://127.0.0.1:3000",
    ]

# Additional CORS settings for UAT
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'

# CORS headers and methods from environment or defaults
CORS_ALLOW_HEADERS_ENV = os.environ.get('CORS_ALLOW_HEADERS', '')
if CORS_ALLOW_HEADERS_ENV:
    # Convert comma-separated string to list
    CORS_ALLOW_HEADERS = [header.strip() for header in CORS_ALLOW_HEADERS_ENV.split(',')]

CORS_ALLOW_METHODS_ENV = os.environ.get('CORS_ALLOW_METHODS', '')
if CORS_ALLOW_METHODS_ENV:
    # Convert comma-separated string to list  
    CORS_ALLOW_METHODS = [method.strip() for method in CORS_ALLOW_METHODS_ENV.split(',')]

# CORS preflight max age
CORS_PREFLIGHT_MAX_AGE_ENV = os.environ.get('CORS_PREFLIGHT_MAX_AGE', '')
if CORS_PREFLIGHT_MAX_AGE_ENV:
    CORS_PREFLIGHT_MAX_AGE = int(CORS_PREFLIGHT_MAX_AGE_ENV)

# Keycloak settings for UAT
KEYCLOAK_CONFIG = {
    'SERVER_URL': os.environ.get('KEYCLOAK_SERVER_URL', 'https://auth.spoton.co.nz'),
    'REALM': os.environ.get('KEYCLOAK_REALM', 'spoton-uat'),
    'CLIENT_ID': os.environ.get('KEYCLOAK_CLIENT_ID', 'customer-uat-portal'),
    'CLIENT_SECRET': os.environ.get('KEYCLOAK_CLIENT_SECRET'),
    'ADMIN_CLIENT_ID': os.environ.get('KEYCLOAK_ADMIN_CLIENT_ID', 'admin-cli'),
    'ADMIN_CLIENT_SECRET': os.environ.get('KEYCLOAK_ADMIN_CLIENT_SECRET', ''),
    'ADMIN_USERNAME': os.environ.get('KEYCLOAK_ADMIN_USERNAME', 'admin'),
    'ADMIN_PASSWORD': os.environ.get('KEYCLOAK_ADMIN_PASSWORD'),
}

# Static files configuration for UAT
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration for UAT
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email configuration for UAT (use console backend for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration for UAT
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django_uat.log',
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utilitybyte': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Cache configuration for UAT (Redis if available, otherwise local memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://:uat_redis_password@spoton-uat-redis:6379/1'),
        'TIMEOUT': 300,
        # Note: CLIENT_CLASS is not compatible with django.core.cache.backends.redis.RedisCache
        # Use django_redis.cache.RedisCache if you need CLIENT_CLASS options
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Security settings for UAT
SECURE_SSL_REDIRECT = False  # Handled by Caddy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TLS = True

# Django extensions for development/debugging in UAT
if DEBUG:
    INSTALLED_APPS += [
    'django_extensions',
    # 'debug_toolbar',  # Temporarily disabled to fix API issues
]


# Ensure debug_toolbar is fully disabled
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

MIDDLEWARE += [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # Temporarily disabled
]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Custom settings for UAT environment
UAT_SPECIFIC_SETTINGS = {
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_DETAILED_LOGGING': True,
    'MOCK_EXTERNAL_SERVICES': False,
    'TEST_DATA_ENABLED': True,
}

# Airflow configuration for UAT
AIRFLOW_CONFIG = {
    'BACKEND_CONTAINER': os.environ.get('BACKEND_CONTAINER', 'spoton-uat-api'),
    'AIRFLOW_ENV': os.environ.get('AIRFLOW_ENV', 'uat'),
    'ENVIRONMENT': os.environ.get('ENVIRONMENT', 'uat'),
}

print(f"🔧 Django settings loaded for UAT environment")
print(f"📊 Database: {DATABASES['default']['NAME']} on {DATABASES['default']['HOST']}")
print(f"🔐 Keycloak Realm: {KEYCLOAK_CONFIG['REALM']}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
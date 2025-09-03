"""
Django settings for Live/Production environment.
"""

import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Environment identifier
ENVIRONMENT = 'live'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'spoton_live'),
        'USER': os.environ.get('DB_USER', 'spoton_live_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'spoton_live_password'),
        'HOST': os.environ.get('DB_HOST', 'spoton-live-db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Allowed hosts for Live environment
ALLOWED_HOSTS = [
    'api.spoton.co.nz',
    'spoton.co.nz',
    'portal.spoton.co.nz',
    'staff.spoton.co.nz',
    'spoton-live-api',
]

# CORS settings for Live (restrictive)
CORS_ALLOWED_ORIGINS = [
    "https://spoton.co.nz",
    "https://portal.spoton.co.nz",
    "https://staff.spoton.co.nz",
]

# Keycloak settings for Live
KEYCLOAK_CONFIG = {
    'SERVER_URL': os.environ.get('KEYCLOAK_SERVER_URL', 'https://auth.spoton.co.nz'),
    'REALM': os.environ.get('KEYCLOAK_REALM', 'spoton-prod'),
    'CLIENT_ID': os.environ.get('KEYCLOAK_CLIENT_ID', 'customer-live-portal'),
    'CLIENT_SECRET': os.environ.get('KEYCLOAK_CLIENT_SECRET'),
    'ADMIN_CLIENT_ID': os.environ.get('KEYCLOAK_ADMIN_CLIENT_ID', 'admin-cli'),
    'ADMIN_CLIENT_SECRET': os.environ.get('KEYCLOAK_ADMIN_CLIENT_SECRET', ''),
    'ADMIN_USERNAME': os.environ.get('KEYCLOAK_ADMIN_USERNAME', 'admin'),
    'ADMIN_PASSWORD': os.environ.get('KEYCLOAK_ADMIN_PASSWORD'),
}

# Static files configuration for Live
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files configuration for Live
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email configuration for Live (use SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@spoton.co.nz')

# Logging configuration for Live
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s", "environment": "live"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django_live.log',
            'formatter': 'json',
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 5,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django_live_errors.log',
            'formatter': 'json',
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 5,
        },
        'console': {
            'level': 'WARNING',
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
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'utilitybyte': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Cache configuration for Live (Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://spoton-live-redis:6379/1'),
        'TIMEOUT': 300,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Security settings for Live
SECURE_SSL_REDIRECT = False  # Handled by Caddy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
USE_TLS = True

# Additional security headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Remove debug-related apps and middleware in production
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in [
    'django_extensions',
    'debug_toolbar',
]]

MIDDLEWARE = [mw for mw in MIDDLEWARE if mw not in [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]]

# Performance optimizations for Live
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5MB

# Database connection pooling (using valid psycopg2 options)
DATABASES['default']['OPTIONS'].update({
    # 'MAX_CONNS': 20,  # Invalid option - removed
    # 'MIN_CONNS': 5,   # Invalid option - removed
    # Connection pooling should be handled at the application level or via pgbouncer
})

# Custom settings for Live environment
LIVE_SPECIFIC_SETTINGS = {
    'ENABLE_DEBUG_TOOLBAR': False,
    'ENABLE_DETAILED_LOGGING': False,
    'MOCK_EXTERNAL_SERVICES': False,
    'TEST_DATA_ENABLED': False,
    'PERFORMANCE_MONITORING': True,
    'SECURITY_MONITORING': True,
}

# Airflow configuration for Live
AIRFLOW_CONFIG = {
    'BACKEND_CONTAINER': os.environ.get('BACKEND_CONTAINER', 'spoton-live-api'),
    'AIRFLOW_ENV': os.environ.get('AIRFLOW_ENV', 'live'),
    'ENVIRONMENT': os.environ.get('ENVIRONMENT', 'live'),
}

# Monitoring and alerting
MONITORING_CONFIG = {
    'ENABLE_METRICS': True,
    'METRICS_ENDPOINT': '/metrics/',
    'HEALTH_CHECK_ENDPOINT': '/health/',
    'ALERT_EMAIL': os.environ.get('ALERT_EMAIL', 'admin@spoton.co.nz'),
}

print(f"🚀 Django settings loaded for LIVE environment")
print(f"📊 Database: {DATABASES['default']['NAME']} on {DATABASES['default']['HOST']}")
print(f"🔐 Keycloak Realm: {KEYCLOAK_CONFIG['REALM']}")
print(f"🌐 Allowed Hosts: {ALLOWED_HOSTS}")
print(f"⚡ Debug Mode: {DEBUG}")
print(f"🔒 Security Headers: Enabled")
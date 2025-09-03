"""
Django settings for Test environment (CI/CD).
"""

import os
from .settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Environment identifier
ENVIRONMENT = 'test'

# Database for testing (in-memory SQLite or test PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_URL', 'test_db').split('/')[-1],
        'USER': os.environ.get('DATABASE_URL', 'postgres://test_user:test_password@localhost:5432/test_db').split('://')[1].split(':')[0],
        'PASSWORD': os.environ.get('DATABASE_URL', 'postgres://test_user:test_password@localhost:5432/test_db').split('://')[1].split(':')[1].split('@')[0],
        'HOST': os.environ.get('DATABASE_URL', 'postgres://test_user:test_password@localhost:5432/test_db').split('@')[1].split(':')[0],
        'PORT': os.environ.get('DATABASE_URL', 'postgres://test_user:test_password@localhost:5432/test_db').split(':')[-1].split('/')[0],
        'TEST': {
            'NAME': 'test_spoton_db',
        }
    }
}

# Use in-memory database for faster tests if PostgreSQL not available
if not os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Allowed hosts for testing
ALLOWED_HOSTS = ['*']

# CORS settings for testing (permissive)
CORS_ALLOW_ALL_ORIGINS = True

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

if os.environ.get('DISABLE_MIGRATIONS'):
    MIGRATION_MODULES = DisableMigrations()

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration for testing (minimal)
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
        'level': 'WARNING',
    },
    'loggers': {
        'django.db.backends': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

# Use local memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Password hashers (faster for testing)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Static files for testing
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files for testing
MEDIA_URL = '/media/'
MEDIA_ROOT = '/tmp/test_media'

# Test-specific settings
TEST_SPECIFIC_SETTINGS = {
    'MOCK_EXTERNAL_SERVICES': True,
    'DISABLE_RATE_LIMITING': True,
    'ENABLE_TEST_DATA': True,
    'FAST_TESTS': True,
}

# Mock Keycloak configuration for testing
KEYCLOAK_CONFIG = {
    'SERVER_URL': 'http://localhost:8080',
    'REALM': 'test-realm',
    'CLIENT_ID': 'test-client',
    'CLIENT_SECRET': 'test-secret',
    'ADMIN_CLIENT_ID': 'admin-cli',
    'ADMIN_CLIENT_SECRET': 'test-admin-secret',
    'ADMIN_USERNAME': 'admin',
    'ADMIN_PASSWORD': 'admin',
}

# Disable security features for testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Test runner configuration
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Add testing-specific apps
INSTALLED_APPS += [
    'django_extensions',
]

# Mock external services for testing
if TEST_SPECIFIC_SETTINGS['MOCK_EXTERNAL_SERVICES']:
    # Add mock service configurations here
    pass

print(f"🧪 Django settings loaded for TEST environment")
print(f"📊 Database: {DATABASES['default'].get('NAME', 'In-memory SQLite')}")
print(f"🔧 Fast tests enabled: {TEST_SPECIFIC_SETTINGS['FAST_TESTS']}")
print(f"🎭 Mock services: {TEST_SPECIFIC_SETTINGS['MOCK_EXTERNAL_SERVICES']}")
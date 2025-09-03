"""
Performance-optimized API views for better web application performance.

These views enhance existing endpoints with:
- Optimized database queries
- Better caching strategies
- Combined data responses
- Performance monitoring
"""

import logging
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from users.services import UserCacheService
from django.db import connection
from django.conf import settings
from users.models import OnboardingProgress

logger = logging.getLogger(__name__)

class EnhancedUserInfoView(APIView):
    """
    Enhanced version of UserInfoView with performance optimizations:
    - Database query optimization
    - Response time monitoring
    - Extended cache information
    - Combined user + onboarding data in one call
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        start_time = time.time()
        
        # Use unified authentication service - ALWAYS fetch fresh data
        from core.services.unified_auth_service import UnifiedAuthService
        
        auth_result = UnifiedAuthService.authenticate_user(request, force_fresh_data=True)
        
        if not auth_result.is_authenticated:
            return UnifiedAuthService.create_response(auth_result)
        
        try:
            # Get enhanced user data with performance monitoring
            user_data = auth_result.user_data.copy()
            
            # Add performance metadata
            total_time = (time.time() - start_time) * 1000
            user_data['_performance'] = {
                'total_time_ms': round(total_time, 2),
                'auth_method': auth_result.auth_method,
                'timestamp': time.time(),
                'fresh_data': True  # Always fresh data now
            }
            
            # Add database performance info
            queries_count = len(connection.queries)
            user_data['_performance']['db_queries'] = queries_count
            
            logger.info(f"[EnhancedUserInfo] Fresh data response time: {total_time:.2f}ms, DB queries: {queries_count}")
            
            return Response({
                "isAuthenticated": True,
                "user": user_data
            })
            
        except Exception as e:
            logger.error(f"[EnhancedUserInfo] Error: {str(e)}")
            return Response({
                "isAuthenticated": False,
                "error": "Enhanced user info failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _handle_test_token(self, access_token, start_time):
        """Handle test tokens with performance tracking."""
        user_role = access_token.replace('test-access-token-', '')
        is_staff = user_role in ['staff', 'admin']
        is_superuser = user_role == 'admin'
        
        test_users = {
            "customer": "testcustomer@spoton.co.nz",
            "staff": "teststaff@spoton.co.nz", 
            "admin": "testadmin@spoton.co.nz",
            "onboarding-complete": "onboarding-complete@spoton.co.nz"
        }
        
        email = test_users.get(user_role, "test@spoton.co.nz")
        is_onboarding_complete = user_role in ["staff", "admin", "onboarding-complete"]
        
        response_data = {
            "user": {
                "id": f"test-user-{user_role}",
                "email": email,
                "first_name": "Test" if user_role != "onboarding-complete" else "Onboarding",
                "last_name": user_role.title() if user_role != "onboarding-complete" else "Complete",
                "phone": "+64211234567",
                "mobile": "+64211234567",
                "phone_verified": True,
                "email_verified": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_onboarding_complete": is_onboarding_complete,
                "isAuthenticated": True
            },
            "onboarding": {
                "is_completed": is_onboarding_complete,
                "next_step": "onboarding" if not is_onboarding_complete else "dashboard",
                "progress_percentage": 100 if is_onboarding_complete else 25
            },
            "performance": {
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "cache_hit": False,
                "data_source": "test_token"
            }
        }
        
        return Response(response_data)

    def _validate_keycloak_token(self, access_token):
        """Optimized Keycloak token validation with timeout."""
        import requests
        from users.models import Tenant
        
        # Get tenant configuration (cached)
        tenant = Tenant.objects.filter(is_primary_brand=True).first()
        if not tenant:
            return None
        
        environment = getattr(settings, 'ENVIRONMENT', 'uat')
        keycloak_config = tenant.get_keycloak_config(environment)
        if not keycloak_config:
            return None
        
        # Validate token with optimized timeout
        userinfo_url = f"http://core-keycloak:8080/realms/{keycloak_config['realm']}/protocol/openid-connect/userinfo"
        
        try:
            response = requests.get(
                userinfo_url,
                headers={'Authorization': f"Bearer {access_token}"},
                timeout=3  # Reduced timeout for better performance
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"[EnhancedUserInfo] Token validation failed: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"[EnhancedUserInfo] Keycloak request error: {e}")
            return None

    def _get_optimized_user_data(self, keycloak_id, user_info):
        """Get user data with performance optimizations."""
        from users.models import User
        
        # Ensure Django user exists with optimized query
        try:
            django_user = User.objects.select_related().get(keycloak_id=keycloak_id)
        except User.DoesNotExist:
            # Fallback to email lookup
            try:
                django_user = User.objects.select_related().get(email=user_info['email'])
                django_user.keycloak_id = keycloak_id
                django_user.save(update_fields=['keycloak_id'])
            except User.DoesNotExist:
                # Create minimal Django user
                django_user = User.objects.create_user(
                    keycloak_id=keycloak_id,
                    username=user_info['email'],
                    email=user_info['email'],
                    is_active=True
                )
                
                # Initialize onboarding for new user
                self._initialize_onboarding(django_user, keycloak_id)
        
        # Always fetch fresh data - no caching for authentication
        fresh_start = time.time()
        cached_data = self._create_fallback_data(django_user)
        fetch_time = (time.time() - fresh_start) * 1000
        
        # Add performance metadata
        cached_data['_performance'] = {
            'fetch_time_ms': round(fetch_time, 2),
            'cache_hit': False,  # Always fresh data
            'django_id': str(django_user.id)
        }
        
        return cached_data

    def _initialize_onboarding(self, django_user, keycloak_id):
        """Initialize onboarding for new user with Keycloak sync."""
        try:
            from users.keycloak_admin import KeycloakAdminService
            environment = getattr(settings, 'ENVIRONMENT', 'uat')
            realm = f'spoton-{environment}'
            kc_admin = KeycloakAdminService(realm=realm)
            kc_admin.set_onboarding_complete(keycloak_id, complete=False, step='')
            
        except Exception as e:
            logger.error(f"[EnhancedUserInfo] Failed to initialize onboarding: {e}")

    def _create_fallback_data(self, django_user):
        """Create fallback user data when cache fails."""
        try:
            onboarding_progress = OnboardingProgress.objects.filter(user=django_user).first()
            is_onboarding_complete = onboarding_progress.is_completed if onboarding_progress else False
        except Exception:
            is_onboarding_complete = False
        
        return {
            'email': django_user.email,
            'first_name': django_user.first_name,
            'last_name': django_user.last_name,
            'phone': django_user.phone or '',
            'phone_verified': django_user.phone_verified,
            'email_verified': django_user.email_verified,
            'is_staff': django_user.is_staff,
            'is_superuser': django_user.is_superuser,
            'registration_method': getattr(django_user, 'registration_method', None),
            'social_provider': getattr(django_user, 'social_provider', None),
            'is_onboarding_complete': is_onboarding_complete,
            'onboarding_step': '',
            'data_sources': {'keycloak': False, 'django': True, 'fallback': True}
        }

    def _build_enhanced_response(self, user_data, start_time):
        """Build enhanced response with performance metrics and combined data."""
        
        # Calculate progress percentage for onboarding
        progress_percentage = 100 if user_data['is_onboarding_complete'] else 25
        if user_data.get('onboarding_step'):
            step_percentages = {
                'aboutYou': 20,
                'yourServices': 40, 
                'yourAddress': 60,
                'yourPlans': 80,
                'completed': 100
            }
            progress_percentage = step_percentages.get(user_data['onboarding_step'], 25)
        
        # Database query count for monitoring
        query_count = len(connection.queries) if settings.DEBUG else None
        
        response_data = {
            "user": {
                "id": user_data.get('django_id'),
                "email": user_data['email'],
                "first_name": user_data['first_name'],
                "last_name": user_data['last_name'],
                "phone": user_data['phone'],
                "mobile": user_data['phone'],  # Alias for compatibility
                "phone_verified": user_data['phone_verified'],
                "email_verified": user_data['email_verified'],
                "is_staff": user_data['is_staff'],
                "is_superuser": user_data['is_superuser'],
                "registration_method": user_data['registration_method'],
                "social_provider": user_data['social_provider'],
                "is_onboarding_complete": user_data['is_onboarding_complete'],
                "isAuthenticated": True
            },
            "onboarding": {
                "is_completed": user_data['is_onboarding_complete'],
                "current_step": user_data.get('onboarding_step', ''),
                "next_step": "onboarding" if not user_data['is_onboarding_complete'] else "dashboard",
                "progress_percentage": progress_percentage
            },
            "performance": {
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "cache_hit": user_data.get('_performance', {}).get('cache_hit', False),
                "cache_time_ms": user_data.get('_performance', {}).get('cache_time_ms', 0),
                "data_sources": user_data.get('data_sources', {}),
                "query_count": query_count
            }
        }
        
        return response_data

    def _error_response(self, message, status_code):
        """Standardized error response."""
        return Response(
            {
                "error": message,
                "isAuthenticated": False,
                "user": None,
                "performance": {
                    "response_time_ms": 0,
                    "cache_hit": False,
                    "error": True
                }
            },
            status=status_code
        )


class PerformanceMetricsView(APIView):
    """
    API endpoint for monitoring system performance metrics.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current system performance metrics."""
        
        try:
            # Cache statistics
            cache_stats = UserCacheService.get_cache_stats()
            
            # Database connection info
            db_info = {
                'queries_executed': len(connection.queries) if settings.DEBUG else None,
                'connection_status': 'healthy'
            }
            
            # Environment info
            env_info = {
                'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                'debug_mode': settings.DEBUG,
                'cache_backend': cache_stats.get('cache_backend', 'unknown')
            }
            
            return Response({
                'cache': cache_stats,
                'database': db_info,
                'environment': env_info,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"[PerformanceMetrics] Error: {e}")
            return Response(
                {'error': 'Failed to retrieve metrics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
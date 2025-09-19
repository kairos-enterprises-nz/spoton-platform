"""
Global authentication coordination views
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core.utils.environment import get_base_urls
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class GlobalLogoutView(APIView):
    """
    Coordinates logout across all SpotOn applications
    Clears cookies with proper domain configuration
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Perform global logout:
        1. Clear JWT cookies with proper domain (.spoton.co.nz)
        2. Clear Django session
        3. Return redirect URLs for all apps
        """
        try:
            logger.info("Starting global logout process")
            
            # Get environment-aware URLs
            base_urls = get_base_urls()
            
            # Create response with success data
            response_data = {
                'success': True,
                'message': 'Global logout successful',
                'redirect_urls': {
                    'marketing': base_urls['web'],
                    'portal': f"{base_urls['portal']}/login",
                    'staff': f"{base_urls['staff']}/login"
                }
            }
            
            response = JsonResponse(response_data, status=200)
            
            # Clear all authentication cookies with proper domain
            self.clear_auth_cookies(response)
            
            # Clear Django session if it exists
            if hasattr(request, 'session'):
                request.session.flush()
                logger.info("Django session cleared")
            
            logger.info("Global logout completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Global logout failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Logout failed: {str(e)}'
            }, status=500)
    
    def clear_auth_cookies(self, response):
        """
        Clear authentication cookies using unified service
        """
        from core.services.auth_cookie_service import clear_auth_cookies
        clear_auth_cookies(response)
        
        # Also clear Django session cookies
        django_cookies = ['sessionid', 'csrftoken']
        for cookie_name in django_cookies:
            # Clear for current domain
            response.set_cookie(
                cookie_name,
                '',
                max_age=0,
                expires='Thu, 01 Jan 1970 00:00:00 GMT',
                path='/',
                secure=True,
                samesite='Lax'
            )
            
            # Clear for .spoton.co.nz domain (cross-subdomain)
            response.set_cookie(
                cookie_name,
                '',
                max_age=0,
                expires='Thu, 01 Jan 1970 00:00:00 GMT',
                path='/',
                domain='.spoton.co.nz',
                secure=True,
                samesite='Lax'
            )
        
        logger.info("🎯 All authentication cookies cleared using unified service")
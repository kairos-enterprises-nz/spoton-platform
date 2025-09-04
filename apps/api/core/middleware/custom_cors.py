"""
Custom CORS middleware that prevents wildcard headers when credentials are used.
"""

from corsheaders.middleware import CorsMiddleware


class CustomCorsMiddleware(CorsMiddleware):
    """
    Custom CORS middleware that overrides the default behavior to prevent
    wildcard Access-Control-Allow-Origin when credentials are enabled.
    """
    
    def add_response_vary_header(self, response):
        """Add Vary header for CORS."""
        super().add_response_vary_header(response)
    
    def process_response(self, request, response):
        """Process the response and ensure no wildcard with credentials."""
        response = super().process_response(request, response)
        
        # If credentials are allowed, never use wildcard
        if hasattr(response, 'get') and response.get('Access-Control-Allow-Credentials') == 'true':
            # Remove any wildcard origins
            if 'Access-Control-Allow-Origin' in response:
                origins = response['Access-Control-Allow-Origin']
                if origins == '*':
                    # Replace wildcard with the actual origin from request
                    origin = request.META.get('HTTP_ORIGIN', '')
                    if origin:
                        response['Access-Control-Allow-Origin'] = origin
                    else:
                        # If no origin, remove the header entirely
                        del response['Access-Control-Allow-Origin']
        
        return response

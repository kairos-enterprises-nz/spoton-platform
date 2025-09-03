class UserInfoView(APIView):
    """
    Get current user information using unified authentication service
    """
    authentication_classes = []  # Bypass DRF authentication - handle manually
    permission_classes = [AllowAny]

    def get(self, request):
        # Use unified authentication service - handles ALL authentication methods
        from core.services.unified_auth_service import UnifiedAuthService
        
        auth_result = UnifiedAuthService.authenticate_user(request)
        
        # Return standardized response
        return UnifiedAuthService.create_response(auth_result)

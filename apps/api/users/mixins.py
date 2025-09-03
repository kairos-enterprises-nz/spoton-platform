from rest_framework.response import Response
from django.conf import settings

API_VERSION = "1.0.0"
BACKEND_VERSION = settings.BACKEND_VERSION

class VersionedViewSetMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if not hasattr(response, 'data') or response.data is None:
            response.data = {}

        version_data = {
            "api_version": API_VERSION,
            "backend_version": BACKEND_VERSION
        }
        
        if isinstance(response.data, dict):
            response.data["version"] = version_data
        
        response['X-API-Version'] = API_VERSION
        response['X-Backend-Version'] = BACKEND_VERSION
        
        return response 
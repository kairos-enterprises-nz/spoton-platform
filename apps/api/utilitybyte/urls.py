"""
URL Configuration for UtilityByte

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("UtilityByte Backend API")

def health_view(request):
    from django.http import JsonResponse
    return JsonResponse({"status": "healthy", "environment": "uat"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('health/', health_view, name='health'),
    
    # OIDC authentication endpoints (disabled - using custom Keycloak)
    # path('oidc/', include('mozilla_django_oidc.urls')),
    
    # Django-allauth authentication endpoints (disabled - using custom Keycloak)
    # path('accounts/', include('allauth.urls')),
    
    # API endpoints - with /api/ prefix for frontend compatibility
    path('api/', include('users.urls')),
    path('api/', include('core.urls')),
    path('api/', include('energy.urls')),
    path('api/', include('finance.urls')),
    path('api/web/', include('web_support.urls')),

    # Staff API (both with and without /api prefix)
    # New canonical path (no extra /api after domain when using api subdomain)
    path('staff/', include('users.staff_urls')),
    # Backward compatible path
    path('api/staff/', include('users.staff_urls')),
    
    # Legacy endpoints without /api/ prefix for backward compatibility
    path('', include('users.urls')),
    path('', include('core.urls')),
    path('', include('energy.urls')),
    path('', include('finance.urls')),
    path('web/', include('web_support.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Add debug toolbar URLs if debug toolbar is installed
    # Temporarily disabled to fix API issues
    # if 'debug_toolbar' in settings.INSTALLED_APPS:
    #     import debug_toolbar
    #     urlpatterns = [
    #         path('__debug__/', include(debug_toolbar.urls)),
    #     ] + urlpatterns
"""
Public schema URLs for tenant management.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public API endpoints (tenant management, health checks, etc.)
    path('health/', views.wiki_health_check, name='health_check'),
    
    # User endpoints that need to be accessible from public schema
    path('check-email/', views.CheckEmail, name='check-email'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Add tenant creation/management endpoints here
] 
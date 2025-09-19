"""
Energy app URLs
"""
from django.urls import path, include

urlpatterns = [
    # Energy app API endpoints
    path('validation/', include('energy.validation.urls')),
    # Other energy endpoints will be added here as needed
] 
"""
Web Support app URLs
"""
from django.urls import path, include
from .address_plans.views import lookup_address, address_summary

urlpatterns = [
    # Direct address endpoints for frontend compatibility
    path('address/', lookup_address, name='web_address_lookup'),
    path('address-summary/', address_summary, name='web_address_summary'),
    
    # Public pricing endpoints
    path('pricing/', include('web_support.public_pricing.urls')),
    
    # Address plans endpoints  
    path('address-plans/', include('web_support.address_plans.urls')),
    
    # Onboarding endpoints
    path('onboarding/', include('web_support.onboarding.urls')),
] 
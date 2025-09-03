# pricing/urls.py
from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    # Service availability
    path('availability/', views.service_availability, name='service_availability'),
    path('regions/', views.pricing_regions, name='pricing_regions'),
    
    # Plan endpoints
    path('electricity/', views.electricity_plans, name='electricity_plans'),
    path('broadband/', views.broadband_plans, name='broadband_plans'),
    path('mobile/', views.mobile_plans, name='mobile_plans'),
    
    # Pricing ID based endpoints
    path('plan/<uuid:pricing_id>/', views.plan_by_pricing_id, name='plan_by_pricing_id'),
    path('plans/bulk/', views.bulk_plans_by_pricing_ids, name='bulk_plans_by_pricing_ids'),
]

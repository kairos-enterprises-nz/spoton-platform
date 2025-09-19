"""
URLs for the energy validation API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ValidationRuleViewSet, ValidationRuleOverrideViewSet, ValidationResultViewSet

router = DefaultRouter()
router.register(r'rules', ValidationRuleViewSet)
router.register(r'overrides', ValidationRuleOverrideViewSet)
router.register(r'exceptions', ValidationResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 
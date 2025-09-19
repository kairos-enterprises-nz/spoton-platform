"""
Finance app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .billing.views import (
    BillingRunViewSet, BillViewSet, ServiceRegistryViewSet,
    BillingCycleViewSet, PaymentViewSet
)
from .invoices.views import InvoiceViewSet

# Create router and register viewsets
router = DefaultRouter()

# Billing endpoints
router.register(r'billing/runs', BillingRunViewSet, basename='billingrun')
router.register(r'billing/bills', BillViewSet, basename='bill')
router.register(r'billing/cycles', BillingCycleViewSet, basename='billingcycle')
router.register(r'billing/registry', ServiceRegistryViewSet, basename='serviceregistry')
router.register(r'billing/payments', PaymentViewSet, basename='payment')

# Invoice endpoints
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('finance/', include(router.urls)),
] 
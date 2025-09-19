from django.urls import path
from .views import UpdateSwitchStatusView, ManualActionView, RegistryMessageView

urlpatterns = [
    path('internal/switches/<uuid:id>/update/', UpdateSwitchStatusView.as_view(), name='update-switch-status'),
    path('switches/<uuid:id>/manual_action/', ManualActionView.as_view(), name='manual-switch-action'),
    path('internal/registry_messages/', RegistryMessageView.as_view(), name='create-registry-message'),
] 
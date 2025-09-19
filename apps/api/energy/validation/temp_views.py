"""
Views for the energy validation API.
"""
from rest_framework import viewsets, permissions
from .models import ValidationRule, ValidationRuleOverride
from .serializers import ValidationRuleSerializer, ValidationRuleOverrideSerializer

class IsStaffUser(permissions.BasePermission):
    """
    Allows access only to staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class ValidationRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows validation rules to be viewed or edited.
    """
    queryset = ValidationRule.objects.all().order_by('name')
    serializer_class = ValidationRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffUser]

class ValidationRuleOverrideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows validation rule overrides to be viewed or edited.
    """
    queryset = ValidationRuleOverride.objects.all().order_by('rule__name')
    serializer_class = ValidationRuleOverrideSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffUser] 
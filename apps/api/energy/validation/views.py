"""
Application layer views - to be configured later

Raw data import is handled by Airflow DAGs → TimescaleDB (direct SQL)
Application views will be configured later for business features.
"""

# Application layer views will be configured later
# Raw data import is handled by Airflow DAGs → TimescaleDB directly

from .models import ValidationRule, ValidationRuleOverride, ValidationResult, ValidationAuditLog
from .serializers import ValidationRuleSerializer, ValidationRuleOverrideSerializer, ValidationResultSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import viewsets
from core.permissions import StaffPermission

class ValidationResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows validation results (failures) to be viewed and acted upon.
    """
    queryset = ValidationResult.objects.filter(final_status='invalid').order_by('-processed_at')
    serializer_class = ValidationResultSerializer
    permission_classes = [StaffPermission]

    @action(detail=True, methods=['post'])
    def override(self, request, pk=None):
        """
        Mark a validation result as overridden.
        """
        try:
            result = self.get_object()
            if result.final_status != 'invalid':
                return Response({'error': 'Only invalid validations can be overridden.'}, status=status.HTTP_400_BAD_REQUEST)

            result.final_status = 'estimated'
            result.save()

            ValidationAuditLog.objects.create(
                user=request.user,
                action='override_created',
                related_result=result,
                details={
                    'result_id': result.id,
                    'meter_id': result.icp_id,
                    'rule_name': result.failed_rules[0] if result.failed_rules else 'N/A'
                }
            )
            
            return Response({'status': 'Validation result overridden'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ValidationRuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows validation rules to be viewed or edited.
    """
    queryset = ValidationRule.objects.all().order_by('name')
    serializer_class = ValidationRuleSerializer
    permission_classes = [StaffPermission]

    def perform_update(self, serializer):
        instance = serializer.save()
        ValidationAuditLog.objects.create(
            user=self.request.user,
            action='rule_updated',
            related_rule=instance,
            details={
                'rule_id': instance.id,
                'rule_name': instance.name,
                'changes': serializer.validated_data
            }
        )

class ValidationRuleOverrideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows validation rule overrides to be viewed or edited.
    """
    queryset = ValidationRuleOverride.objects.all()
    serializer_class = ValidationRuleOverrideSerializer
    permission_classes = [StaffPermission]

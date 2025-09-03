"""
Serializers for plan and connection assignments
"""

from rest_framework import serializers
from core.contracts.plan_assignments import ContractPlanAssignment, ContractConnectionAssignment
from core.contracts.models import ServiceContract
from users.models import User, Tenant


class ContractPlanAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for contract plan assignments"""
    
    # Contract details
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_service_name = serializers.CharField(source='contract.service_name', read_only=True)
    contract_status = serializers.CharField(source='contract.status', read_only=True)
    
    # Account details
    account_number = serializers.CharField(source='contract.account.account_number', read_only=True)
    account_name = serializers.CharField(source='contract.account.account_name', read_only=True)
    
    # Tenant details
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    # Assignment details
    assigned_by_name = serializers.SerializerMethodField()
    registry_plan_details = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ContractPlanAssignment
        fields = [
            'id', 'tenant', 'tenant_name', 'contract', 'contract_number', 
            'contract_service_name', 'contract_status', 'account_number', 'account_name',
            'plan_type', 'plan_id', 'plan_name', 'assigned_date', 'assigned_by', 'assigned_by_name',
            'valid_from', 'valid_to', 'is_active', 'registry_plan_details', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_assigned_by_name(self, obj):
        """Get the name of the user who made the assignment"""
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip()
        return None
    
    def get_registry_plan_details(self, obj):
        """Get details from the registry plan"""
        registry_plan = obj.registry_plan
        if not registry_plan:
            return None
        
        # Common fields for all plan types
        details = {
            'plan_id': registry_plan.plan_id,
            'name': registry_plan.name,
            'description': getattr(registry_plan, 'description', ''),
            'plan_type': obj.plan_type,
            'is_active': getattr(registry_plan, 'is_active', True),
        }
        
        # Add type-specific details
        if obj.plan_type == 'electricity':
            details.update({
                'base_rate': float(getattr(registry_plan, 'base_rate', 0) or 0),
                'daily_charge': float(getattr(registry_plan, 'standard_daily_charge', 0) or 0),
                'pricing_details': f'${getattr(registry_plan, "base_rate", 0)}/kWh + ${getattr(registry_plan, "standard_daily_charge", 0)}/day',
                'term': getattr(registry_plan, 'term', 'open_term'),
            })
        elif obj.plan_type == 'broadband':
            details.update({
                'monthly_cost': float(getattr(registry_plan, 'monthly_cost', 0) or 0),
                'speed': getattr(registry_plan, 'speed', ''),
                'data_limit': getattr(registry_plan, 'data_limit', 'unlimited'),
            })
        elif obj.plan_type == 'mobile':
            details.update({
                'monthly_cost': float(getattr(registry_plan, 'monthly_cost', 0) or 0),
                'data_allowance': getattr(registry_plan, 'data_allowance', ''),
                'call_minutes': getattr(registry_plan, 'call_minutes', ''),
            })
        
        return details


class ContractConnectionAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for contract connection assignments"""
    
    # Contract details
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_service_name = serializers.CharField(source='contract.service_name', read_only=True)
    contract_status = serializers.CharField(source='contract.status', read_only=True)
    
    # Connection details
    connection_details = serializers.SerializerMethodField()
    
    # Account details
    account_number = serializers.CharField(source='contract.account.account_number', read_only=True)
    account_name = serializers.CharField(source='contract.account.account_name', read_only=True)
    
    # Tenant details
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    # Assignment details
    assigned_by_name = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ContractConnectionAssignment
        fields = [
            'id', 'tenant', 'tenant_name', 'contract', 'contract_number',
            'contract_service_name', 'contract_status', 'account_number', 'account_name',
            'connection_id', 'connection_details', 'assigned_date', 'assigned_by', 'assigned_by_name',
            'valid_from', 'valid_to', 'status', 'is_active', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_assigned_by_name(self, obj):
        """Get the name of the user who made the assignment"""
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip()
        return None
    
    def get_connection_details(self, obj):
        """Get details from the connection"""
        connection = obj.connection
        if not connection:
            return {
                'connection_id': str(obj.connection_id),
                'status': 'not_found',
                'error': 'Connection not found'
            }
        
        return {
            'id': str(connection.id),
            'connection_identifier': connection.connection_identifier,
            'service_type': connection.service_type,
            'status': connection.status,
            'icp_code': getattr(connection, 'icp_code', None),
            'ont_serial': getattr(connection, 'ont_serial', None),
            'mobile_number': getattr(connection, 'mobile_number', None),
            'service_address': {
                'address_line1': connection.service_address.address_line1 if connection.service_address else None,
                'city': connection.service_address.city if connection.service_address else None,
                'postal_code': connection.service_address.postal_code if connection.service_address else None,
            } if connection.service_address else None,
            'valid_from': connection.valid_from.isoformat() if connection.valid_from else None,
            'valid_to': connection.valid_to.isoformat() if connection.valid_to else None,
            'is_active': connection.is_active,
        }


class ContractPlanAssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    account_number = serializers.CharField(source='contract.account.account_number', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ContractPlanAssignment
        fields = [
            'id', 'tenant_name', 'contract_number', 'account_number',
            'plan_type', 'plan_id', 'plan_name', 'assigned_date', 'assigned_by_name',
            'valid_from', 'valid_to', 'is_active', 'created_at'
        ]
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip()
        return None


class ContractConnectionAssignmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    account_number = serializers.CharField(source='contract.account.account_number', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    connection_identifier = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ContractConnectionAssignment
        fields = [
            'id', 'tenant_name', 'contract_number', 'account_number',
            'connection_id', 'connection_identifier', 'service_type', 'assigned_date', 'assigned_by_name',
            'valid_from', 'valid_to', 'status', 'is_active', 'created_at'
        ]
    
    def get_connection_identifier(self, obj):
        connection = obj.connection
        return connection.connection_identifier if connection else f"Connection-{str(obj.connection_id)[:8]}"
    
    def get_service_type(self, obj):
        connection = obj.connection
        return connection.service_type if connection else 'unknown'
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}".strip()
        return None
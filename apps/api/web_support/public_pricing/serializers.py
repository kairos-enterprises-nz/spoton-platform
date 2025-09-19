from rest_framework import serializers
from .models import ElectricityPlan, BroadbandPlan, MobilePlan


class ElectricityPlanSerializer(serializers.ModelSerializer):
    service_type = serializers.SerializerMethodField()
    
    class Meta:
        model = ElectricityPlan
        fields = [
            'id', 'pricing_id', 'plan_id', 'name', 'plan_type', 'description',
            'term', 'city', 'base_rate', 'rate_details', 'standard_daily_charge',
            'standard_variable_charge', 'low_user_daily_charge', 'low_user_variable_charge',
            'peak_charge', 'off_peak_charge', 'is_active', 'created_at', 'updated_at',
            'service_type'
        ]
        read_only_fields = ['id', 'pricing_id', 'created_at', 'updated_at']
    
    def get_service_type(self, obj):
        return 'electricity'


class BroadbandPlanSerializer(serializers.ModelSerializer):
    service_type = serializers.SerializerMethodField()
    
    class Meta:
        model = BroadbandPlan
        fields = [
            'id', 'pricing_id', 'plan_id', 'name', 'plan_type', 'description',
            'term', 'city', 'base_rate', 'rate_details', 'monthly_charge',
            'setup_fee', 'data_allowance', 'download_speed', 'upload_speed',
            'is_active', 'created_at', 'updated_at', 'service_type'
        ]
        read_only_fields = ['id', 'pricing_id', 'created_at', 'updated_at']
    
    def get_service_type(self, obj):
        return 'broadband'


class MobilePlanSerializer(serializers.ModelSerializer):
    service_type = serializers.SerializerMethodField()
    call_minutes = serializers.CharField(source='minutes', read_only=True)
    text_messages = serializers.CharField(source='texts', read_only=True)
    
    class Meta:
        model = MobilePlan
        fields = [
            'id', 'pricing_id', 'plan_id', 'name', 'plan_type', 'description',
            'term', 'city', 'base_rate', 'rate_details', 'monthly_charge',
            'setup_fee', 'data_allowance', 'call_minutes', 'text_messages',
            'is_active', 'created_at', 'updated_at', 'service_type'
        ]
        read_only_fields = ['id', 'pricing_id', 'created_at', 'updated_at']
    
    def get_service_type(self, obj):
        return 'mobile'


class ConnectionSerializer(serializers.Serializer):
    """
    Serializer for sample connection data
    """
    id = serializers.UUIDField(read_only=True)
    service_type = serializers.CharField()
    connection_identifier = serializers.CharField()
    status = serializers.CharField()
    icp_code = serializers.CharField(required=False, allow_blank=True)
    mobile_number = serializers.CharField(required=False, allow_blank=True)
    ont_serial = serializers.CharField(required=False, allow_blank=True)
    circuit_id = serializers.CharField(required=False, allow_blank=True)
    connection_type = serializers.CharField(required=False, allow_blank=True)
    service_details = serializers.JSONField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Related data
    account = serializers.DictField(required=False)
    plan = serializers.DictField(required=False) 
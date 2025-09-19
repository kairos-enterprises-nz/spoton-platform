"""
Serializers for the energy validation app.
"""
from rest_framework import serializers
from .models import ValidationRule, ValidationRuleOverride, ValidationResult

class ValidationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for the ValidationRule model.
    """
    class Meta:
        model = ValidationRule
        fields = '__all__'

class ValidationRuleOverrideSerializer(serializers.ModelSerializer):
    """
    Serializer for the ValidationRuleOverride model.
    """
    class Meta:
        model = ValidationRuleOverride
        fields = '__all__'

class ValidationResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the ValidationResult model.
    """
    class Meta:
        model = ValidationResult
        fields = '__all__' 
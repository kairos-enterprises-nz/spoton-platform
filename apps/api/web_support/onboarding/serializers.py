from rest_framework import serializers
from users.models import OnboardingProgress

class OnboardingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingProgress
        fields = ['current_step', 'step_data',]

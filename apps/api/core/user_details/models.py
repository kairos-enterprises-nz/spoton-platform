# user_details/models.py

from django.db import models
from django.conf import settings


class UserOnboardingConfirmation(models.Model):
    """
    Comprehensive onboarding completion data for backend processing.
    This stores all the essential information needed to initiate backend tasks.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='onboarding_confirmation')
    
    # Essential address information (not full plan details)
    address_info = models.JSONField(default=dict, blank=True, help_text="Essential address info: full_address, service availability")
    
    # Service selections and chosen plans
    services_chosen = models.JSONField(default=dict, blank=True, help_text="Selected services: mobile, broadband, electricity")
    plan_selections = models.JSONField(default=dict, blank=True, help_text="Selected plans for each service")
    
    # Personal information from aboutYou step
    personal_info = models.JSONField(default=dict, blank=True, help_text="DOB, ID details, contact preferences")
    
    # Service-specific details for backend processing
    service_details = models.JSONField(default=dict, blank=True, help_text="Service start dates, transfer types, device preferences")
    
    # Payment and preferences
    payment_info = models.JSONField(default=dict, blank=True, help_text="Payment method and billing preferences")
    notification_preferences = models.JSONField(default=dict, blank=True, help_text="Communication preferences")
    
    # Completion tracking
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OnboardingConfirmation for {self.user.email}"

class UserPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    
    notification_preferences = models.JSONField(default=dict, blank=True)
    communication_preferences = models.JSONField(default=dict, blank=True)
    
    # Service interest preferences for future notifications
    interested_in_mobile = models.BooleanField(default=False, help_text="User wants to be notified when mobile services become available")
    interested_in_power = models.BooleanField(default=False, help_text="User wants to be notified when power services become available")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.email}"

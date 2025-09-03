from django.urls import path
from .views import OnboardingProgressView, OnboardingFinalizeView
from .temp_selection_views import save_temp_selection, get_temp_selection

urlpatterns = [
    path('progress/', OnboardingProgressView.as_view(), name='onboarding-progress'),
    path('finalize/', OnboardingFinalizeView.as_view(), name='onboarding-finalize'),
    path('save-temp-selection/', save_temp_selection, name='save-temp-selection'),
    path('get-temp-selection/<str:session_id>/', get_temp_selection, name='get-temp-selection'),
]

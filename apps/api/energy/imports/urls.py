from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    # Import statistics and monitoring
    path('statistics/', views.import_statistics, name='import_statistics'),
    path('health/', views.system_health, name='system_health'),
    path('data-sources/', views.data_sources_status, name='data_sources_status'),
] 
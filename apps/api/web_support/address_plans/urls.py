from django.urls import path
from .views import lookup_address, address_summary

urlpatterns = [
    path('address/', lookup_address, name='lookup_address'),
    path("address-summary/", address_summary),

]
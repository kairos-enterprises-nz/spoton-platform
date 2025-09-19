from django.http import JsonResponse
from .models import Address
from rapidfuzz import process
import json
import random
import requests
import logging
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import jwt

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .utils import get_electricity_plans, get_broadband_plans
from .constants import ELECTRICITY_CITIES, BROADBAND_CITIES

logger = logging.getLogger(__name__)

## For Address Verification

@api_view(['GET'])
@authentication_classes([])  # Bypass DRF authentication
@permission_classes([AllowAny])
def lookup_address(request):
    query = request.GET.get('query', '').strip()

    if not query:
        return JsonResponse({"error": "No query provided."}, status=400)

    # Perform an initial DB lookup (Limit to 25 results to optimize performance)
    addresses = Address.objects.filter(full_address__icontains=query).values_list('full_address', flat=True)[:25]

    if not addresses:
        return JsonResponse({"results": []}, status=200)  # No results found

    # Perform fuzzy matching only on the limited dataset
    matches = process.extract(query, addresses, limit=5)

    # Convert results into a JSON response
    results = [{"full_address": match[0]} for match in matches]

    return JsonResponse({"results": results}, status=200)



## For Service Availability

@api_view(['GET'])
@authentication_classes([])  # Bypass DRF authentication
@permission_classes([AllowAny])
def address_summary(request):
    query = request.GET.get('query')
    if not query:
        return Response({'status': 'error', 'message': 'Address query is required'}, status=400)

    # Search for address in the database
    address = Address.objects.filter(full_address__icontains=query).first()
    if not address:
        return Response({'status': 'error', 'message': 'Address not found'}, status=404)

    city = address.town_city.strip().lower()
    try:
        from web_support.public_pricing.models import PricingRegion
        from web_support.public_pricing.utils import (
            get_electricity_plans_by_pricing_ids,
            get_broadband_plans_by_pricing_ids
        )
        try:
            region = PricingRegion.objects.get(city=city, is_active=True)
            electricity_available = region.electricity_available
            broadband_available = region.broadband_available
            
            # Safely get plans with database error handling
            electricity_plans = []
            broadband_plans = []
            
            if electricity_available:
                try:
                    electricity_plans = get_electricity_plans_by_pricing_ids(address)
                except Exception as e:
                    logger.warning(f"Failed to get electricity plans: {e}")
                    electricity_plans = []
            
            if broadband_available:
                try:
                    broadband_plans = get_broadband_plans_by_pricing_ids(address)
                except Exception as e:
                    logger.warning(f"Failed to get broadband plans: {e}")
                    broadband_plans = []
            
            data = {
                "status": "available" if electricity_available or broadband_available else "unavailable",
                "electricity": {
                    "available": electricity_available,
                    "plans": electricity_plans
                },
                "broadband": {
                    "available": broadband_available,
                    "plans": broadband_plans
                }
            }
            return Response(data)
        except PricingRegion.DoesNotExist:
            # No region found, mark as unavailable
            data = {
                "status": "unavailable",
                "electricity": {"available": False, "plans": []},
                "broadband": {"available": False, "plans": []}
            }
            return Response(data)
        except Exception as e:
            # Handle any database or other errors gracefully
            logger.error(f"Error in address_summary: {e}")
            data = {
                "status": "unavailable",
                "electricity": {"available": False, "plans": []},
                "broadband": {"available": False, "plans": []}
            }
            return Response(data)
    except ImportError:
        return Response({'status': 'error', 'message': 'Pricing app not available'}, status=500)
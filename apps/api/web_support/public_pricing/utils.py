# pricing/utils.py
from .models import ElectricityPlan, BroadbandPlan, PricingRegion, MobilePlan
import logging

logger = logging.getLogger(__name__)


def get_electricity_plans_by_pricing_ids(address, pricing_ids=None):
    """
    Get electricity plans using pricing IDs for scalable pricing lookup
    
    Args:
        address: Address object containing city information
        pricing_ids: List of pricing IDs to filter plans (optional)
    
    Returns:
        List of electricity plan data
    """
    city = address.town_city.strip().lower()
    
    # Base query for active plans in the city
    queryset = ElectricityPlan.objects.filter(
        city=city,
        is_active=True
    )
    
    # Filter by pricing IDs if provided
    if pricing_ids:
        queryset = queryset.filter(pricing_id__in=pricing_ids)
    
    plans = []
    for plan in queryset:
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "description": plan.description,
            "term": plan.get_term_display(),
            "terms_url": plan.terms_url,
            "rate": float(plan.base_rate),
            "rate_details": plan.rate_details,
            "charges": plan.get_charges_data()
        }
        plans.append(plan_data)
    
    return plans


def get_broadband_plans_by_pricing_ids(address, pricing_ids=None):
    """
    Get broadband plans using pricing IDs for scalable pricing lookup
    
    Args:
        address: Address object containing city information
        pricing_ids: List of pricing IDs to filter plans (optional)
    
    Returns:
        List of broadband plan data
    """
    city = address.town_city.strip().lower()
    
    # Base query for active plans in the city
    queryset = BroadbandPlan.objects.filter(
        city=city,
        is_active=True
    )
    
    # Filter by pricing IDs if provided
    if pricing_ids:
        queryset = queryset.filter(pricing_id__in=pricing_ids)
    
    plans = []
    for plan in queryset:
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "description": plan.description,
            "term": plan.get_term_display(),
            "terms_url": plan.terms_url,
            "rate": float(plan.base_rate),
            "rate_details": plan.rate_details,
            "charges": plan.get_charges_data()
        }
        
        # Add service specifications if available
        if plan.data_allowance:
            plan_data["data_allowance"] = plan.data_allowance
        if plan.download_speed:
            plan_data["download_speed"] = plan.download_speed
        if plan.upload_speed:
            plan_data["upload_speed"] = plan.upload_speed
            
        plans.append(plan_data)
    
    return plans


def get_mobile_plans_by_pricing_ids(address, pricing_ids=None):
    """Get mobile plans by pricing IDs"""
    try:
        query = MobilePlan.objects.filter(is_active=True)
        
        if pricing_ids:
            if isinstance(pricing_ids, str):
                pricing_ids = pricing_ids.split(',')
            query = query.filter(pricing_id__in=pricing_ids)
        else:
            city = address.town_city.strip().lower()
            query = query.filter(city__iexact=city)
        
        plans = []
        for plan in query:
            plan_data = {
                'pricing_id': str(plan.pricing_id),
                'plan_id': plan.plan_id,
                'name': plan.name,
                'plan_type': plan.plan_type,
                'description': plan.description,
                'term': plan.term,
                'terms_url': plan.terms_url,
                'rate': float(plan.monthly_charge),
                'rate_details': plan.rate_details,
                'charges': plan.get_charges_data()
            }
            plans.append(plan_data)
        
        return plans
    except Exception as e:
        logger.error(f"Error getting mobile plans: {str(e)}")
        return []


def get_mobile_plans(address):
    """Get all mobile plans for an address"""
    return get_mobile_plans_by_pricing_ids(address)


def get_service_availability_by_city(city):
    """Get service availability for a city"""
    try:
        region = PricingRegion.objects.filter(
            city__iexact=city,
            is_active=True
        ).first()
        
        if not region:
            return {
                'city': city.capitalize(),
                'electricity_available': False,
                'broadband_available': False,
                'mobile_available': False
            }
        
        return {
            'city': region.display_name,
            'electricity_available': region.electricity_available,
            'broadband_available': region.broadband_available,
            'mobile_available': region.mobile_available
        }
    except Exception as e:
        logger.error(f"Error getting service availability: {str(e)}")
        return {
            'city': city.capitalize(),
            'electricity_available': False,
            'broadband_available': False,
            'mobile_available': False
        }


def get_all_available_cities():
    """
    Get all cities with active pricing regions
    
    Returns:
        QuerySet of PricingRegion objects
    """
    return PricingRegion.objects.filter(is_active=True)


# Backward compatibility functions for existing API
def get_electricity_plans(address):
    """
    Backward compatible function - returns all electricity plans for address
    """
    return get_electricity_plans_by_pricing_ids(address)


def get_broadband_plans(address):
    """
    Backward compatible function - returns all broadband plans for address
    """
    return get_broadband_plans_by_pricing_ids(address)

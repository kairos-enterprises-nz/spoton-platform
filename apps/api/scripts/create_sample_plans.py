#!/usr/bin/env python3
"""
Script to create sample plan data for testing the plan assignment system
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/arun-kumar/Dev/Spoton_Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from web_support.public_pricing.models import ElectricityPlan, BroadbandPlan, MobilePlan
from django.utils import timezone
from decimal import Decimal

def create_sample_plans():
    """Create sample plans for all service types"""
    
    print("Creating sample electricity plans...")
    
    # Electricity Plans
    electricity_plans = [
        {
            'plan_id': 1,
            'name': 'SpotOn Fixed Electricity',
            'plan_type': 'fixed',
            'description': 'Fixed rate electricity plan with competitive pricing',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/electricity-fixed',
            'city': 'wellington',
            'base_rate': Decimal('0.25'),
            'rate_details': 'Fixed daily charge plus unit rate',
            'standard_daily_charge': Decimal('1.50'),
            'standard_variable_charge': Decimal('0.25'),
            'low_user_daily_charge': Decimal('1.20'),
            'low_user_variable_charge': Decimal('0.28'),
            'is_active': True
        },
        {
            'plan_id': 2,
            'name': 'SpotOn Green Electricity',
            'plan_type': 'fixed',
            'description': '100% renewable electricity plan',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/electricity-green',
            'city': 'wellington',
            'base_rate': Decimal('0.28'),
            'rate_details': '100% renewable energy with fixed rates',
            'standard_daily_charge': Decimal('1.60'),
            'standard_variable_charge': Decimal('0.28'),
            'low_user_daily_charge': Decimal('1.30'),
            'low_user_variable_charge': Decimal('0.31'),
            'is_active': True
        },
        {
            'plan_id': 3,
            'name': 'SpotOn Time of Use',
            'plan_type': 'tou',
            'description': 'Time of use electricity plan with peak/off-peak rates',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/electricity-tou',
            'city': 'wellington',
            'base_rate': Decimal('0.22'),
            'rate_details': 'Different rates for peak and off-peak times',
            'standard_daily_charge': Decimal('1.40'),
            'peak_charge': Decimal('0.35'),
            'off_peak_charge': Decimal('0.18'),
            'low_user_daily_charge': Decimal('1.10'),
            'low_user_peak_charge': Decimal('0.38'),
            'low_user_off_peak_charge': Decimal('0.21'),
            'is_active': True
        }
    ]
    
    for plan_data in electricity_plans:
        plan, created = ElectricityPlan.objects.get_or_create(
            plan_id=plan_data['plan_id'],
            defaults=plan_data
        )
        if created:
            print(f"Created electricity plan: {plan.name}")
        else:
            print(f"Electricity plan already exists: {plan.name}")
    
    print("\nCreating sample broadband plans...")
    
    # Broadband Plans
    broadband_plans = [
        {
            'plan_id': 3,
            'name': 'SpotOn Fibre Basic',
            'plan_type': 'fibre',
            'description': 'Basic fibre broadband for everyday use',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/broadband-basic',
            'city': 'wellington',
            'base_rate': Decimal('69.99'),
            'rate_details': 'Unlimited data with 100/20 Mbps speeds',
            'monthly_charge': Decimal('69.99'),
            'setup_fee': Decimal('0.00'),
            'data_allowance': 'Unlimited',
            'download_speed': '100 Mbps',
            'upload_speed': '20 Mbps',
            'is_active': True
        },
        {
            'plan_id': 4,
            'name': 'SpotOn Fibre Pro',
            'plan_type': 'fibre',
            'description': 'High-speed fibre for families and professionals',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/broadband-pro',
            'city': 'wellington',
            'base_rate': Decimal('89.99'),
            'rate_details': 'Unlimited data with 300/100 Mbps speeds',
            'monthly_charge': Decimal('89.99'),
            'setup_fee': Decimal('0.00'),
            'data_allowance': 'Unlimited',
            'download_speed': '300 Mbps',
            'upload_speed': '100 Mbps',
            'is_active': True
        },
        {
            'plan_id': 5,
            'name': 'SpotOn Fibre Max',
            'plan_type': 'fibre',
            'description': 'Maximum speed fibre for power users',
            'term': '24_month',
            'terms_url': 'https://spoton.co.nz/terms/broadband-max',
            'city': 'wellington',
            'base_rate': Decimal('129.99'),
            'rate_details': 'Unlimited data with 1000/500 Mbps speeds',
            'monthly_charge': Decimal('129.99'),
            'setup_fee': Decimal('99.00'),
            'data_allowance': 'Unlimited',
            'download_speed': '1000 Mbps',
            'upload_speed': '500 Mbps',
            'is_active': True
        }
    ]
    
    for plan_data in broadband_plans:
        plan, created = BroadbandPlan.objects.get_or_create(
            plan_id=plan_data['plan_id'],
            defaults=plan_data
        )
        if created:
            print(f"Created broadband plan: {plan.name}")
        else:
            print(f"Broadband plan already exists: {plan.name}")
    
    print("\nCreating sample mobile plans...")
    
    # Mobile Plans
    mobile_plans = [
        {
            'plan_id': 5,
            'name': 'SpotOn Mobile Essential',
            'plan_type': 'prepaid',
            'description': 'Essential mobile plan with good data allowance',
            'term': 'open_term',
            'terms_url': 'https://spoton.co.nz/terms/mobile-essential',
            'city': 'nz',
            'base_rate': Decimal('29.99'),
            'rate_details': '5GB data with unlimited calls and texts',
            'monthly_charge': Decimal('29.99'),
            'data_allowance': '5GB',
            'minutes': 'Unlimited',
            'texts': 'Unlimited',
            'setup_fee': Decimal('0.00'),
            'sim_card_fee': Decimal('5.00'),
            'data_rate': Decimal('10.00'),
            'minute_rate': Decimal('0.00'),
            'text_rate': Decimal('0.00'),
            'international_minutes': '0',
            'international_texts': '0',
            'international_data': '0',
            'hotspot_data': '5GB',
            'rollover_data': False,
            'data_speed': 'Full Speed',
            'is_active': True
        },
        {
            'plan_id': 6,
            'name': 'SpotOn Mobile Plus',
            'plan_type': 'postpaid',
            'description': 'Popular mobile plan with generous data',
            'term': '12_month',
            'terms_url': 'https://spoton.co.nz/terms/mobile-plus',
            'city': 'nz',
            'base_rate': Decimal('49.99'),
            'rate_details': '20GB data with unlimited calls and texts',
            'monthly_charge': Decimal('49.99'),
            'data_allowance': '20GB',
            'minutes': 'Unlimited',
            'texts': 'Unlimited',
            'setup_fee': Decimal('0.00'),
            'sim_card_fee': Decimal('0.00'),
            'data_rate': Decimal('10.00'),
            'minute_rate': Decimal('0.00'),
            'text_rate': Decimal('0.00'),
            'international_minutes': '100',
            'international_texts': '100',
            'international_data': '1GB',
            'hotspot_data': '20GB',
            'rollover_data': True,
            'data_speed': 'Full Speed',
            'is_active': True
        },
        {
            'plan_id': 7,
            'name': 'SpotOn Mobile Business',
            'plan_type': 'business',
            'description': 'Business mobile plan with premium features',
            'term': '24_month',
            'terms_url': 'https://spoton.co.nz/terms/mobile-business',
            'city': 'nz',
            'base_rate': Decimal('79.99'),
            'rate_details': '50GB data with unlimited calls and premium support',
            'monthly_charge': Decimal('79.99'),
            'data_allowance': '50GB',
            'minutes': 'Unlimited',
            'texts': 'Unlimited',
            'setup_fee': Decimal('0.00'),
            'sim_card_fee': Decimal('0.00'),
            'data_rate': Decimal('5.00'),
            'minute_rate': Decimal('0.00'),
            'text_rate': Decimal('0.00'),
            'international_minutes': 'Unlimited',
            'international_texts': 'Unlimited',
            'international_data': '10GB',
            'hotspot_data': '50GB',
            'rollover_data': True,
            'data_speed': 'Full Speed',
            'is_active': True
        }
    ]
    
    for plan_data in mobile_plans:
        plan, created = MobilePlan.objects.get_or_create(
            plan_id=plan_data['plan_id'],
            defaults=plan_data
        )
        if created:
            print(f"Created mobile plan: {plan.name}")
        else:
            print(f"Mobile plan already exists: {plan.name}")
    
    print("\nSample plans creation completed!")
    
    # Print summary
    print(f"\nSummary:")
    print(f"Electricity plans: {ElectricityPlan.objects.filter(is_active=True).count()}")
    print(f"Broadband plans: {BroadbandPlan.objects.filter(is_active=True).count()}")
    print(f"Mobile plans: {MobilePlan.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    create_sample_plans() 
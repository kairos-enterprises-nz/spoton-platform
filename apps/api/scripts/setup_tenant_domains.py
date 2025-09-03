#!/usr/bin/env python3
"""
Setup script for configuring django-tenants domain entries
Ensures all required hostnames are properly mapped to tenants
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from users.models import Client, Domain

def setup_required_domains():
    """Configure all required domain entries for the SpotOn Energy system"""
    
    print("🔧 Setting up tenant domains for SpotOn Energy...")
    
    # Get or create public schema client
    public_client, created = Client.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Public Schema',
            'description': 'Public schema for shared resources and authentication'
        }
    )
    
    if created:
        print(f"✅ Created public client: {public_client.name}")
    else:
        print(f"✅ Found existing public client: {public_client.name}")
    
    # Required domains for Docker/development setup
    required_domains = [
        'localhost',           # Local development
        'backend',            # Docker inter-container communication
        '192.168.1.107',      # Network IP
        '192.168.1.107:8000', # Network IP with port
        '127.0.0.1',          # Localhost IP
        '0.0.0.0',            # All interfaces
    ]
    
    created_count = 0
    for domain_name in required_domains:
        domain, created = Domain.objects.get_or_create(
            domain=domain_name,
            defaults={
                'tenant': public_client,
                'is_primary': (domain_name == 'localhost')
            }
        )
        
        if created:
            print(f"✅ Created domain: {domain_name} -> {public_client.name}")
            created_count += 1
        else:
            print(f"ℹ️  Domain exists: {domain_name} -> {domain.tenant.name}")
    
    print(f"\n🎉 Setup complete! Created {created_count} new domain(s)")
    
    # Display current domain configuration
    print("\n📋 Current domain configuration:")
    print("-" * 50)
    for domain in Domain.objects.all().order_by('domain'):
        primary = " (PRIMARY)" if domain.is_primary else ""
        print(f"  {domain.domain} -> {domain.tenant.name}{primary}")
    print("-" * 50)

def verify_api_access():
    """Verify that API endpoints are accessible"""
    import requests
    
    print("\n🧪 Testing API endpoint access...")
    
    test_endpoints = [
        'http://localhost:8000/api/users/check-email/?email=test@example.com',
        'http://backend:8000/api/users/check-email/?email=test@example.com',
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK")
            else:
                print(f"⚠️  {endpoint} - HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - ERROR: {e}")

if __name__ == "__main__":
    try:
        setup_required_domains()
        verify_api_access()
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1) 
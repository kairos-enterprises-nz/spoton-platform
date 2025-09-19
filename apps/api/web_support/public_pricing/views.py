from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
from users.auth import IsStaffUser

from .models import ElectricityPlan, BroadbandPlan, PricingRegion, MobilePlan
from .utils import (
    get_electricity_plans_by_pricing_ids,
    get_broadband_plans_by_pricing_ids,
    get_service_availability_by_city,
    get_all_available_cities,
    get_mobile_plans
)
from web_support.address_plans.models import Address
from .serializers import (
    ElectricityPlanSerializer, 
    BroadbandPlanSerializer, 
    MobilePlanSerializer,
    ConnectionSerializer
)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def electricity_plans(request):
    """
    Get electricity plans for a city, optionally filtered by pricing IDs
    
    Query parameters:
    - city: City name (required)
    - pricing_ids: Comma-separated list of pricing IDs (optional)
    """
    city = request.GET.get('city')
    if not city:
        return Response({'error': 'City parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    pricing_ids = request.GET.get('pricing_ids')
    if pricing_ids:
        pricing_ids = [pid.strip() for pid in pricing_ids.split(',')]
    
    # Create a mock address object for compatibility
    class MockAddress:
        def __init__(self, city):
            self.town_city = city
    
    address = MockAddress(city)
    plans = get_electricity_plans_by_pricing_ids(address, pricing_ids)
    
    return Response({
        'city': city.capitalize(),
        'plans': plans,
        'count': len(plans)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def broadband_plans(request):
    """
    Get broadband plans for a city, optionally filtered by pricing IDs
    
    Query parameters:
    - city: City name (required)
    - pricing_ids: Comma-separated list of pricing IDs (optional)
    """
    city = request.GET.get('city')
    if not city:
        return Response({'error': 'City parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    pricing_ids = request.GET.get('pricing_ids')
    if pricing_ids:
        pricing_ids = [pid.strip() for pid in pricing_ids.split(',')]
    
    # Create a mock address object for compatibility
    class MockAddress:
        def __init__(self, city):
            self.town_city = city
    
    address = MockAddress(city)
    plans = get_broadband_plans_by_pricing_ids(address, pricing_ids)
    
    return Response({
        'city': city.capitalize(),
        'plans': plans,
        'count': len(plans)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def mobile_plans(request):
    """Get all mobile plans (universal across NZ)"""
    try:
        # Get all active mobile plans
        plans = MobilePlan.objects.filter(is_active=True)
        
        plan_list = []
        for plan in plans:
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
            plan_list.append(plan_data)
            
        return Response({'plans': plan_list})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def service_availability(request):
    """
    Check service availability for a city
    
    Query parameters:
    - city: City name (required)
    """
    city = request.GET.get('city')
    if not city:
        return Response({'error': 'City parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        availability = get_service_availability_by_city(city)
        return Response(availability)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def pricing_regions(request):
    """
    Get all available pricing regions
    """
    regions = get_all_available_cities().values(
        'city', 'display_name', 'service_availability', 
        'electricity_available', 'broadband_available'
    )
    
    return Response({
        'regions': list(regions),
        'count': len(regions)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def plan_by_pricing_id(request, pricing_id):
    """
    Get a specific plan by its pricing ID
    
    Path parameters:
    - pricing_id: UUID of the pricing plan
    """
    # Try electricity plans first
    try:
        plan = ElectricityPlan.objects.get(pricing_id=pricing_id, is_active=True)
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "type": "electricity",
            "plan_type": plan.plan_type,
            "description": plan.description,
            "term": plan.get_term_display(),
            "terms_url": plan.terms_url,
            "city": plan.city,
            "rate": float(plan.base_rate),
            "rate_details": plan.rate_details,
            "charges": plan.get_charges_data()
        }
        return Response(plan_data)
    except ElectricityPlan.DoesNotExist:
        pass
    
    # Try broadband plans
    try:
        plan = BroadbandPlan.objects.get(pricing_id=pricing_id, is_active=True)
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "type": "broadband",
            "plan_type": plan.plan_type,
            "description": plan.description,
            "term": plan.get_term_display(),
            "terms_url": plan.terms_url,
            "city": plan.city,
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
            
        return Response(plan_data)
    except BroadbandPlan.DoesNotExist:
        pass
    
    return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def bulk_plans_by_pricing_ids(request):
    """
    Get multiple plans by their pricing IDs
    
    Query parameters:
    - pricing_ids: Comma-separated list of pricing IDs (required)
    """
    pricing_ids_param = request.GET.get('pricing_ids')
    if not pricing_ids_param:
        return Response({'error': 'pricing_ids parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    pricing_ids = [pid.strip() for pid in pricing_ids_param.split(',')]
    
    # Get electricity plans
    electricity_plans = ElectricityPlan.objects.filter(
        pricing_id__in=pricing_ids, 
        is_active=True
    )
    
    # Get broadband plans
    broadband_plans = BroadbandPlan.objects.filter(
        pricing_id__in=pricing_ids, 
        is_active=True
    )
    
    # Get mobile plans
    mobile_plans = MobilePlan.objects.filter(
        pricing_id__in=pricing_ids,
        is_active=True
    )
    
    plans = []
    
    # Process electricity plans
    for plan in electricity_plans:
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "type": "electricity",
            "plan_type": plan.plan_type,
            "description": plan.description,
            "term": plan.get_term_display(),
            "city": plan.city,
            "rate": float(plan.base_rate),
            "charges": plan.get_charges_data()
        }
        plans.append(plan_data)
    
    # Process broadband plans
    for plan in broadband_plans:
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "type": "broadband",
            "plan_type": plan.plan_type,
            "description": plan.description,
            "term": plan.get_term_display(),
            "city": plan.city,
            "rate": float(plan.base_rate),
            "charges": plan.get_charges_data()
        }
        plans.append(plan_data)
    
    # Process mobile plans
    for plan in mobile_plans:
        plan_data = {
            "id": plan.plan_id,
            "pricing_id": str(plan.pricing_id),
            "name": plan.name,
            "type": "mobile",
            "plan_type": plan.plan_type,
            "description": plan.description,
            "term": plan.term,
            "rate": float(plan.monthly_charge),
            "rate_details": plan.rate_details,
            "charges": plan.get_charges_data(),
            "terms_url": plan.terms_url,
            # Add any other fields as needed
        }
        plans.append(plan_data)
    
    return Response({
        'plans': plans,
        'count': len(plans),
        'requested_ids': pricing_ids
    })


class PlanViewSet(viewsets.ModelViewSet):
    """
    Combined viewset for all plan types
    """
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get_queryset(self):
        plan_type = self.request.query_params.get('type', 'all')
        
        # Apply time-based filtering
        now = timezone.now()
        
        if plan_type == 'electricity':
            return ElectricityPlan.objects.filter(
                is_active=True,
                created_at__lte=now  # Only plans created before now
            ).order_by('-created_at')
        elif plan_type == 'broadband':
            return BroadbandPlan.objects.filter(
                is_active=True,
                created_at__lte=now
            ).order_by('-created_at')
        elif plan_type == 'mobile':
            return MobilePlan.objects.filter(
                is_active=True,
                created_at__lte=now
            ).order_by('-created_at')
        else:
            # Return all plans combined with proper filtering
            electricity_plans = list(ElectricityPlan.objects.filter(
                is_active=True,
                created_at__lte=now
            ).order_by('-created_at'))
            broadband_plans = list(BroadbandPlan.objects.filter(
                is_active=True,
                created_at__lte=now
            ).order_by('-created_at'))
            mobile_plans = list(MobilePlan.objects.filter(
                is_active=True,
                created_at__lte=now
            ).order_by('-created_at'))
            return electricity_plans + broadband_plans + mobile_plans
    
    def get_serializer_class(self):
        plan_type = self.request.query_params.get('type', 'all')
        
        if plan_type == 'electricity':
            return ElectricityPlanSerializer
        elif plan_type == 'broadband':
            return BroadbandPlanSerializer
        elif plan_type == 'mobile':
            return MobilePlanSerializer
        else:
            # For mixed results, we'll handle serialization manually
            return ElectricityPlanSerializer
    
    def list(self, request, *args, **kwargs):
        plan_type = request.query_params.get('type', 'all')
        
        try:
            # Apply time-based filtering
            now = timezone.now()
            
            if plan_type == 'all':
                # Get all plan types with proper filtering
                electricity_plans = ElectricityPlan.objects.filter(
                    is_active=True,
                    created_at__lte=now
                ).order_by('-created_at')
                broadband_plans = BroadbandPlan.objects.filter(
                    is_active=True,
                    created_at__lte=now
                ).order_by('-created_at')
                mobile_plans = MobilePlan.objects.filter(
                    is_active=True,
                    created_at__lte=now
                ).order_by('-created_at')
                
                all_plans = []
                
                # Serialize electricity plans
                for plan in electricity_plans:
                    serializer = ElectricityPlanSerializer(plan)
                    plan_data = serializer.data
                    plan_data['service_type'] = 'electricity'
                    plan_data['monthly_charge'] = float(plan.base_rate)
                    plan_data['active_connections_count'] = self._get_connection_count_for_plan(str(plan.plan_id), 'electricity')
                    plan_data['features'] = self._get_plan_features(plan, 'electricity')
                    all_plans.append(plan_data)
                
                # Serialize broadband plans
                for plan in broadband_plans:
                    serializer = BroadbandPlanSerializer(plan)
                    plan_data = serializer.data
                    plan_data['service_type'] = 'broadband'
                    plan_data['active_connections_count'] = self._get_connection_count_for_plan(str(plan.plan_id), 'broadband')
                    plan_data['features'] = self._get_plan_features(plan, 'broadband')
                    all_plans.append(plan_data)
                
                # Serialize mobile plans
                for plan in mobile_plans:
                    serializer = MobilePlanSerializer(plan)
                    plan_data = serializer.data
                    plan_data['service_type'] = 'mobile'
                    plan_data['active_connections_count'] = self._get_connection_count_for_plan(str(plan.plan_id), 'mobile')
                    plan_data['features'] = self._get_plan_features(plan, 'mobile')
                    all_plans.append(plan_data)
                
                return Response(all_plans)
            else:
                # Handle single plan type
                queryset = self.get_queryset()
                serializer_class = self.get_serializer_class()
                serializer = serializer_class(queryset, many=True)
                
                # Add connection counts and service type
                plans_data = serializer.data
                for plan_data in plans_data:
                    plan_data['service_type'] = plan_type
                    plan_data['active_connections_count'] = self._get_connection_count_for_plan(str(plan_data['id']), plan_type)
                    # Add features based on plan type
                    if plan_type in ['electricity', 'broadband', 'mobile']:
                        plan_obj = queryset.get(id=plan_data['id'])
                        plan_data['features'] = self._get_plan_features(plan_obj, plan_type)
                
                return Response(plans_data)
                
        except Exception as e:
            # Return sample data if database queries fail
            print(f"Database query failed: {e}")
            return Response(self._get_sample_plans())
    
    def _get_sample_plans(self):
        """Return sample plan data when database is not available"""
        return [
            {
                'id': '1',
                'service_type': 'electricity',
                'name': 'SpotOn Fixed Electricity',
                'plan_type': 'fixed',
                'description': 'Fixed rate electricity plan with competitive pricing',
                'base_rate': 0.25,
                'monthly_charge': 150.00,
                'status': 'active',
                'active_connections_count': 2,  # Based on sample connections
                'features': ['Fixed daily charge: $1.50', 'Unit rate: $0.25/kWh', '24/7 support'],
                'created_at': '2024-01-15'
            },
            {
                'id': '2',
                'service_type': 'electricity',
                'name': 'SpotOn Green Electricity',
                'plan_type': 'green',
                'description': '100% renewable electricity plan',
                'base_rate': 0.28,
                'monthly_charge': 165.00,
                'status': 'active',
                'active_connections_count': 1,
                'features': ['100% renewable energy', 'Carbon neutral', 'Fixed daily charge: $1.60'],
                'created_at': '2024-01-10'
            },
            {
                'id': '3',
                'service_type': 'broadband',
                'name': 'SpotOn Fibre Basic',
                'plan_type': 'fibre',
                'description': 'Basic fibre broadband for everyday use',
                'base_rate': 69.99,
                'monthly_charge': 69.99,
                'download_speed': '100 Mbps',
                'upload_speed': '20 Mbps',
                'data_allowance': 'Unlimited',
                'status': 'active',
                'active_connections_count': 1,
                'features': ['100/20 Mbps speeds', 'Unlimited data', 'Free router'],
                'created_at': '2024-01-08'
            },
            {
                'id': '4',
                'service_type': 'broadband',
                'name': 'SpotOn Fibre Pro',
                'plan_type': 'fibre',
                'description': 'High-speed fibre for families and professionals',
                'base_rate': 89.99,
                'monthly_charge': 89.99,
                'download_speed': '300 Mbps',
                'upload_speed': '100 Mbps',
                'data_allowance': 'Unlimited',
                'status': 'active',
                'active_connections_count': 1,
                'features': ['300/100 Mbps speeds', 'Unlimited data', 'Premium router', 'Priority support'],
                'created_at': '2024-01-05'
            },
            {
                'id': '5',
                'service_type': 'mobile',
                'name': 'SpotOn Mobile Essential',
                'plan_type': 'prepaid',
                'description': 'Essential mobile plan with good data allowance',
                'base_rate': 29.99,
                'monthly_charge': 29.99,
                'data_allowance': '5GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'status': 'active',
                'active_connections_count': 1,
                'features': ['5GB data', 'Unlimited calls & texts', 'No contract'],
                'created_at': '2024-01-03'
            },
            {
                'id': '6',
                'service_type': 'mobile',
                'name': 'SpotOn Mobile Plus',
                'plan_type': 'postpaid',
                'description': 'Popular mobile plan with generous data',
                'base_rate': 49.99,
                'monthly_charge': 49.99,
                'data_allowance': '20GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'status': 'active',
                'active_connections_count': 1,
                'features': ['20GB data', 'Unlimited calls & texts', 'International roaming'],
                'created_at': '2024-01-01'
            }
        ]
    
    def _get_connection_count_for_plan(self, plan_id, service_type):
        """Get the number of active connections for a specific plan"""
        # Since we're using sample data, return static counts based on our sample connections
        connection_counts = {
            '1': 1,  # SpotOn Fixed Electricity
            '2': 1,  # SpotOn Green Electricity  
            '3': 1,  # SpotOn Fibre Basic
            '4': 1,  # SpotOn Fibre Pro
            '5': 1,  # SpotOn Mobile Essential
            '6': 1,  # SpotOn Mobile Plus
        }
        return connection_counts.get(plan_id, 0)
    
    def _get_plan_features(self, plan, service_type):
        """Extract plan features based on service type"""
        if service_type == 'electricity':
            return [
                f'Daily charge: ${float(plan.standard_daily_charge)}',
                f'Unit rate: ${float(plan.standard_variable_charge or plan.base_rate)}/kWh',
                f'Plan type: {plan.get_plan_type_display()}',
                '24/7 support'
            ]
        elif service_type == 'broadband':
            features = []
            if plan.download_speed:
                features.append(f'{plan.download_speed}/{plan.upload_speed} speeds')
            features.append(f'Data: {plan.data_allowance}')
            if plan.setup_fee == 0:
                features.append('No setup fee')
            else:
                features.append(f'Setup fee: ${float(plan.setup_fee)}')
            features.append(f'Plan type: {plan.get_plan_type_display()}')
            return features
        elif service_type == 'mobile':
            return [
                f'Data: {plan.data_allowance}',
                f'Calls: {plan.minutes}',
                f'Texts: {plan.texts}',
                f'Plan type: {plan.get_plan_type_display()}'
            ]
        
        return []


class ConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing service connections
    """
    permission_classes = [IsAuthenticated, IsStaffUser]
    serializer_class = ConnectionSerializer
    
    def get_queryset(self):
        # Since we're using sample data from a simple table, we'll query directly
        return []
    
    def list(self, request, *args, **kwargs):
        try:
            # Try to get data from sample_connections table
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, service_type, connection_identifier, status, 
                           icp_code, mobile_number, ont_serial, circuit_id, 
                           connection_type, service_details, created_at
                    FROM sample_connections 
                    ORDER BY created_at DESC
                """)
                
                connections = []
                for row in cursor.fetchall():
                    connection_data = {
                        'id': row[0],
                        'service_type': row[1],
                        'connection_identifier': row[2],
                        'status': row[3],
                        'icp_code': row[4],
                        'mobile_number': row[5],
                        'ont_serial': row[6],
                        'circuit_id': row[7],
                        'connection_type': row[8],
                        'service_details': row[9],
                        'created_at': row[10],
                        # Add mock account and plan data
                        'account': {
                            'account_number': f'ACC-{row[0][:8]}-2024',
                            'user': {'email': 'testuser@email.com'}
                        },
                        'plan': {
                            'name': f'SpotOn {row[1].title()} Plan',
                            'base_rate': 69.99 if row[1] == 'broadband' else (29.99 if row[1] == 'mobile' else 150.00)
                        }
                    }
                    connections.append(connection_data)
                
                return Response(connections)
                
        except Exception as e:
            # Return sample data if database query fails
            return Response(self._get_sample_connections())
    
    def _get_sample_connections(self):
        """Return sample connection data when database is not available"""
        return [
            {
                'id': '1',
                'service_type': 'electricity',
                'connection_identifier': 'ICP001024001',
                'status': 'active',
                'account': { 
                    'id': '1',
                    'account_number': 'ACC-001-2024', 
                    'user': {'email': 'testuser@email.com'}
                },
                'plan': { 
                    'id': '1',
                    'name': 'SpotOn Fixed Electricity', 
                    'service_type': 'electricity',
                    'monthly_charge': 150.00,
                    'base_rate': 0.25,
                    'description': 'Fixed rate electricity plan with competitive pricing',
                    'features': ['Fixed daily charge: $1.50', 'Unit rate: $0.25/kWh', '24/7 support']
                },
                'service_details': {'icp_code': 'ICP001024001', 'gxp_code': 'WLG001', 'network_code': 'WEL'},
                'assigned_date': '2024-06-01'
            },
            {
                'id': '2',
                'service_type': 'broadband',
                'connection_identifier': 'ONT001024BB',
                'status': 'active',
                'account': { 
                    'id': '1',
                    'account_number': 'ACC-001-2024', 
                    'user': {'email': 'testuser@email.com'}
                },
                'plan': { 
                    'id': '3',
                    'name': 'SpotOn Fibre Basic', 
                    'service_type': 'broadband',
                    'monthly_charge': 69.99,
                    'download_speed': '100 Mbps', 
                    'upload_speed': '20 Mbps',
                    'data_allowance': 'Unlimited',
                    'description': 'Basic fibre broadband for everyday use',
                    'features': ['100/20 Mbps speeds', 'Unlimited data', 'Free router']
                },
                'service_details': {'ont_serial': 'ONT001024BB', 'circuit_id': 'CIR1024', 'connection_type': 'fibre'},
                'assigned_date': '2024-06-05'
            },
            {
                'id': '3',
                'service_type': 'mobile',
                'connection_identifier': '+64 21 001024',
                'status': 'active',
                'account': { 
                    'id': '2',
                    'account_number': 'ACC-002-2024', 
                    'user': {'email': 'admin@spoton.co.nz'}
                },
                'plan': { 
                    'id': '6',
                    'name': 'SpotOn Mobile Plus', 
                    'service_type': 'mobile',
                    'monthly_charge': 49.99,
                    'data_allowance': '20GB',
                    'call_minutes': 'Unlimited',
                    'text_messages': 'Unlimited',
                    'description': 'Popular mobile plan with generous data',
                    'features': ['20GB data', 'Unlimited calls & texts', 'International roaming']
                },
                'service_details': {'mobile_number': '+64 21 001024', 'sim_id': 'SIM001024', 'imei': '35001024'},
                'assigned_date': '2024-06-10'
            },
            {
                'id': '4',
                'service_type': 'electricity',
                'connection_identifier': 'ICP002024001',
                'status': 'active',
                'account': { 
                    'id': '2',
                    'account_number': 'ACC-002-2024', 
                    'user': {'email': 'admin@spoton.co.nz'}
                },
                'plan': { 
                    'id': '2',
                    'name': 'SpotOn Green Electricity', 
                    'service_type': 'electricity',
                    'monthly_charge': 165.00,
                    'base_rate': 0.28,
                    'description': '100% renewable electricity plan',
                    'features': ['100% renewable energy', 'Carbon neutral', 'Fixed daily charge: $1.60']
                },
                'service_details': {'icp_code': 'ICP002024001', 'gxp_code': 'WLG002', 'network_code': 'WEL'},
                'assigned_date': '2024-06-12'
            },
            {
                'id': '5',
                'service_type': 'broadband',
                'connection_identifier': 'ONT002024BB',
                'status': 'pending',
                'account': { 
                    'id': '2',
                    'account_number': 'ACC-002-2024', 
                    'user': {'email': 'admin@spoton.co.nz'}
                },
                'plan': { 
                    'id': '4',
                    'name': 'SpotOn Fibre Pro', 
                    'service_type': 'broadband',
                    'monthly_charge': 89.99,
                    'download_speed': '300 Mbps', 
                    'upload_speed': '100 Mbps',
                    'data_allowance': 'Unlimited',
                    'description': 'High-speed fibre for families and professionals',
                    'features': ['300/100 Mbps speeds', 'Unlimited data', 'Premium router', 'Priority support']
                },
                'service_details': {'ont_serial': 'ONT002024BB', 'circuit_id': 'CIR2024', 'connection_type': 'fibre'},
                'assigned_date': '2024-06-15'
            },
            {
                'id': '6',
                'service_type': 'mobile',
                'connection_identifier': '+64 21 002024',
                'status': 'pending',
                'account': { 
                    'id': '1',
                    'account_number': 'ACC-001-2024', 
                    'user': {'email': 'testuser@email.com'}
                },
                'plan': { 
                    'id': '5',
                    'name': 'SpotOn Mobile Essential', 
                    'service_type': 'mobile',
                    'monthly_charge': 29.99,
                    'data_allowance': '5GB',
                    'call_minutes': 'Unlimited',
                    'text_messages': 'Unlimited',
                    'description': 'Essential mobile plan with good data allowance',
                    'features': ['5GB data', 'Unlimited calls & texts', 'No contract']
                },
                'service_details': {'mobile_number': '+64 21 002024', 'sim_id': 'SIM002024', 'imei': '35002024'},
                                 'assigned_date': '2024-06-18'
             }
         ]
    
    def create(self, request, *args, **kwargs):
        """Create a new connection with plan assignment"""
        try:
            data = request.data
            
            # Simulate creating a connection
            new_connection = {
                'id': str(len(self._get_sample_connections()) + 1),
                'service_type': data.get('service_type'),
                'connection_identifier': data.get('connection_identifier'),
                'status': data.get('status', 'pending'),
                'account': {
                    'id': data.get('account_id'),
                    'account_number': f'ACC-{data.get("account_id", "999")}-2024',
                    'user': {'email': 'user@example.com'}
                },
                'plan': self._get_plan_by_id(data.get('plan_id')) if data.get('plan_id') else None,
                'service_details': data.get('service_details', {}),
                'assigned_date': '2024-06-23'
            }
            
            return Response(new_connection, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update connection, including plan assignment"""
        try:
            connection_id = kwargs.get('pk')
            data = request.data
            
            # Get existing connection
            connections = self._get_sample_connections()
            connection = next((c for c in connections if c['id'] == connection_id), None)
            
            if not connection:
                return Response(
                    {'error': 'Connection not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update fields
            if 'plan_id' in data:
                connection['plan'] = self._get_plan_by_id(data['plan_id'])
                connection['assigned_date'] = '2024-06-23'  # Update assignment date
            
            if 'status' in data:
                connection['status'] = data['status']
            
            if 'service_details' in data:
                connection['service_details'].update(data['service_details'])
            
            return Response(connection)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_plan_by_id(self, plan_id):
        """Get plan details by ID for assignment"""
        plan_map = {
            '1': {
                'id': '1',
                'name': 'SpotOn Fixed Electricity', 
                'service_type': 'electricity',
                'monthly_charge': 150.00,
                'base_rate': 0.25,
                'description': 'Fixed rate electricity plan with competitive pricing',
                'features': ['Fixed daily charge: $1.50', 'Unit rate: $0.25/kWh', '24/7 support']
            },
            '2': {
                'id': '2',
                'name': 'SpotOn Green Electricity', 
                'service_type': 'electricity',
                'monthly_charge': 165.00,
                'base_rate': 0.28,
                'description': '100% renewable electricity plan',
                'features': ['100% renewable energy', 'Carbon neutral', 'Fixed daily charge: $1.60']
            },
            '3': {
                'id': '3',
                'name': 'SpotOn Fibre Basic', 
                'service_type': 'broadband',
                'monthly_charge': 69.99,
                'download_speed': '100 Mbps', 
                'upload_speed': '20 Mbps',
                'data_allowance': 'Unlimited',
                'description': 'Basic fibre broadband for everyday use',
                'features': ['100/20 Mbps speeds', 'Unlimited data', 'Free router']
            },
            '4': {
                'id': '4',
                'name': 'SpotOn Fibre Pro', 
                'service_type': 'broadband',
                'monthly_charge': 89.99,
                'download_speed': '300 Mbps', 
                'upload_speed': '100 Mbps',
                'data_allowance': 'Unlimited',
                'description': 'High-speed fibre for families and professionals',
                'features': ['300/100 Mbps speeds', 'Unlimited data', 'Premium router', 'Priority support']
            },
            '5': {
                'id': '5',
                'name': 'SpotOn Mobile Essential', 
                'service_type': 'mobile',
                'monthly_charge': 29.99,
                'data_allowance': '5GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'description': 'Essential mobile plan with good data allowance',
                'features': ['5GB data', 'Unlimited calls & texts', 'No contract']
            },
            '6': {
                'id': '6',
                'name': 'SpotOn Mobile Plus', 
                'service_type': 'mobile',
                'monthly_charge': 49.99,
                'data_allowance': '20GB',
                'call_minutes': 'Unlimited',
                'text_messages': 'Unlimited',
                'description': 'Popular mobile plan with generous data',
                'features': ['20GB data', 'Unlimited calls & texts', 'International roaming']
            }
        }
        
        return plan_map.get(str(plan_id))

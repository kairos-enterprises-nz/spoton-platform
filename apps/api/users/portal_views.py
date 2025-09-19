# users/portal_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.utils import timezone
from core.services.unified_auth_service import UnifiedAuthService
from core.user_details.models import UserOnboardingConfirmation
from users.models import OnboardingProgress
import logging

logger = logging.getLogger(__name__)

class UserPortalDataView(APIView):
    """
    Comprehensive user data endpoint for portal dashboard.
    Returns real user data from onboarding process instead of mock data.
    """
    
    def get(self, request):
        try:
            # Get authenticated user using unified auth service
            auth_result = UnifiedAuthService.authenticate_user(request)
            
            if not auth_result.is_authenticated:
                return Response(
                    {'error': 'Authentication required', 'details': auth_result.error}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = auth_result.user
            user_data = auth_result.user_data or {}
            
            logger.info(f"[UserPortalDataView] Fetching portal data for user {user.id}")
            
            # Get onboarding confirmation data
            portal_data = {
                'user_profile': self._get_user_profile(user, user_data),
                'services': self._get_user_services(user),
                'billing': self._get_billing_info(user),
                'personal_details': self._get_personal_details(user),
                'preferences': self._get_user_preferences(user),
                'account_summary': self._get_account_summary(user),
            }
            
            logger.info(f"[UserPortalDataView] Successfully fetched portal data for user {user.id}")
            return Response(portal_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[UserPortalDataView] Error fetching portal data: {str(e)}")
            return Response(
                {'error': 'Failed to fetch user data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_profile(self, user, user_data):
        """Get user profile information"""
        try:
            confirmation = UserOnboardingConfirmation.objects.get(user=user)
            personal_info = confirmation.personal_info or {}
        except UserOnboardingConfirmation.DoesNotExist:
            personal_info = {}
        
        return {
            'id': str(user.id),
            'name': user_data.get('first_name', '') + ' ' + user_data.get('last_name', ''),
            'first_name': user_data.get('first_name', ''),
            'last_name': user_data.get('last_name', ''),
            'email': user_data.get('email', ''),
            'mobile': user_data.get('mobile', ''),
            'account_number': f"AC{str(user.id)[-6:].zfill(6)}",
            'user_type': personal_info.get('accountType', 'Residential'),
            'registration_method': user_data.get('registration_method', 'email'),
            'social_provider': user_data.get('social_provider', ''),
            'date_joined': confirmation.completed_at.isoformat() if hasattr(confirmation, 'completed_at') else timezone.now().isoformat(),
        }
    
    def _get_user_services(self, user):
        """Get user's actual services from contracts and connections"""
        try:
            # Get user's account
            from users.models import UserAccountRole
            user_role = UserAccountRole.objects.filter(user=user).select_related('account').first()
            if not user_role:
                logger.warning(f"[UserPortalDataView] No account found for user {user.id}")
                return self._get_fallback_services(user)
            
            account = user_role.account
            
            # Get active contracts for this account
            from core.contracts.models import ServiceContract
            from energy.connections.models import Connection
            
            contracts = ServiceContract.objects.filter(
                account=account,
                status__in=['pending', 'active']
            ).select_related('account').prefetch_related('account__connections')
            
            # Get connections for this account
            connections = Connection.objects.filter(account=account)
            
            # Build service data from real contracts
            active_services = []
            service_plans = {}
            service_statuses = {}
            
            for contract in contracts:
                service_type = contract.contract_type
                active_services.append(service_type)
                
                # Get plan details from contract metadata
                plan_data = contract.metadata.get('plan', {}) if contract.metadata else {}
                service_plans[service_type] = {
                    'name': contract.service_name,
                    'rate': float(contract.base_charge),
                    'monthly_charge': float(contract.base_charge),
                    'status': contract.status,
                    'contract_id': str(contract.id),
                    'start_date': contract.start_date.isoformat(),
                    **plan_data  # Include original plan data from onboarding
                }
                
                # Get connection status
                connection = connections.filter(
                    contract_id=contract.id,
                    service_type=service_type
                ).first()
                
                if connection:
                    service_statuses[service_type] = {
                        'status': connection.status,
                        'connection_id': str(connection.id),
                        'identifier': connection.connection_identifier,
                        'metadata': connection.metadata or {}
                    }
            
            # If no contracts found, use fallback to onboarding data
            if not active_services:
                logger.info(f"[UserPortalDataView] No contracts found for user {user.id}, using fallback onboarding data")
                return self._get_fallback_services(user)
            
            # Get service address from account
            service_address = {}
            if account.billing_address:
                addr = account.billing_address
                service_address = {
                    'full_address': f"{addr.address_line1}, {addr.city}",
                    'address_line1': addr.address_line1,
                    'city': addr.city,
                    'postal_code': addr.postal_code,
                    'suburb': addr.suburb,
                    'region': addr.region,
                }
            
            logger.info(f"[UserPortalDataView] Found {len(active_services)} active services for user {user.id}: {active_services}")
            logger.info(f"[UserPortalDataView] Contract details for user {user.id}:")
            for contract in contracts:
                logger.info(f"  - Contract {contract.id}: {contract.contract_type} | {contract.status} | {contract.service_name}")
            logger.info(f"[UserPortalDataView] Connection details for user {user.id}:")
            for connection in connections:
                logger.info(f"  - Connection {connection.id}: {connection.service_type} | {connection.status} | contract_id={connection.contract_id}")
            
            return {
                'active_services': active_services,
                'services_chosen': {service: True for service in active_services},
                'selected_plans': service_plans,
                'service_address': service_address,
                'service_statuses': service_statuses,
                'total_services': len(active_services),
                'account_id': str(account.id),
                'account_number': account.account_number,
            }
            
        except Exception as e:
            logger.error(f"[UserPortalDataView] Error fetching real services for user {user.id}: {str(e)}")
            return self._get_fallback_services(user)
    
    def _get_fallback_services(self, user):
        """Fallback to onboarding data if no contracts found"""
        try:
            confirmation = UserOnboardingConfirmation.objects.get(user=user)
            services_chosen = confirmation.services_chosen or {}
            plan_selections = confirmation.plan_selections or {}
            address_info = confirmation.address_info or {}
            
            # Extract active services
            active_services = []
            for service_type in ['mobile', 'broadband', 'electricity']:
                if services_chosen.get(service_type, False):
                    active_services.append(service_type)
            
            logger.info(f"[UserPortalDataView] Using fallback onboarding data for user {user.id}: {active_services}")
            
            return {
                'active_services': active_services,
                'services_chosen': services_chosen,
                'selected_plans': plan_selections,
                'service_address': address_info,
                'service_statuses': {},
                'total_services': len(active_services),
            }
            
        except UserOnboardingConfirmation.DoesNotExist:
            logger.warning(f"[UserPortalDataView] No onboarding confirmation found for user {user.id}")
            return {
                'active_services': [],
                'services_chosen': {},
                'selected_plans': {},
                'service_address': {},
                'service_statuses': {},
                'total_services': 0,
            }
    
    def _get_billing_info(self, user):
        """Get user's billing and payment information"""
        try:
            confirmation = UserOnboardingConfirmation.objects.get(user=user)
            payment_info = confirmation.payment_info or {}
            
            # Calculate estimated monthly bill from selected plans
            plan_selections = confirmation.plan_selections or {}
            total_monthly_cost = 0
            
            for service_type, plan_data in plan_selections.items():
                if isinstance(plan_data, dict):
                    monthly_charge = 0
                    
                    # Extract monthly charge from different plan structures
                    if 'monthly_charge' in plan_data:
                        monthly_charge = float(plan_data['monthly_charge'])
                    elif 'rate' in plan_data:
                        monthly_charge = float(plan_data['rate'])
                    elif 'charges' in plan_data and isinstance(plan_data['charges'], dict):
                        charges = plan_data['charges']
                        if 'monthly_charge' in charges:
                            monthly_charge = float(charges['monthly_charge'])
                    
                    total_monthly_cost += monthly_charge
            
            return {
                'payment_method': payment_info.get('paymentMethodType', 'Not specified'),
                'payment_details': payment_info,
                'estimated_monthly_bill': round(total_monthly_cost, 2),
                'billing_preferences': confirmation.notification_preferences or {},
                'next_bill_date': None,  # Would be calculated based on service start dates
                'account_balance': 0.00,  # Would come from billing system
            }
            
        except UserOnboardingConfirmation.DoesNotExist:
            return {
                'payment_method': 'Not specified',
                'payment_details': {},
                'estimated_monthly_bill': 0.00,
                'billing_preferences': {},
                'next_bill_date': None,
                'account_balance': 0.00,
            }
    
    def _get_personal_details(self, user):
        """Get user's personal information from onboarding"""
        try:
            confirmation = UserOnboardingConfirmation.objects.get(user=user)
            return confirmation.personal_info or {}
        except UserOnboardingConfirmation.DoesNotExist:
            return {}
    
    def _get_user_preferences(self, user):
        """Get user's notification and communication preferences"""
        try:
            confirmation = UserOnboardingConfirmation.objects.get(user=user)
            return confirmation.notification_preferences or {}
        except UserOnboardingConfirmation.DoesNotExist:
            return {}
    
    def _get_account_summary(self, user):
        """Get account summary information"""
        services = self._get_user_services(user)
        billing = self._get_billing_info(user)
        
        return {
            'total_services': services['total_services'],
            'monthly_bill': billing['estimated_monthly_bill'],
            'account_status': 'Active',
            'next_payment_due': 0,  # Would be calculated from billing system
        }


class UserServiceDetailsView(APIView):
    """
    Get detailed information for a specific service
    """
    
    def get(self, request, service_type):
        try:
            # Get authenticated user using unified auth service
            auth_result = UnifiedAuthService.authenticate_user(request)
            
            if not auth_result.is_authenticated:
                return Response(
                    {'error': 'Authentication required', 'details': auth_result.error}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = auth_result.user
            
            # Validate service type
            if service_type not in ['mobile', 'broadband', 'electricity']:
                return Response(
                    {'error': 'Invalid service type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                confirmation = UserOnboardingConfirmation.objects.get(user=user)
                
                # Check if user has this service
                services_chosen = confirmation.services_chosen or {}
                if not services_chosen.get(service_type, False):
                    return Response(
                        {'error': f'User does not have {service_type} service'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Get plan details
                plan_selections = confirmation.plan_selections or {}
                service_details = confirmation.service_details or {}
                
                service_data = {
                    'service_type': service_type,
                    'is_active': True,
                    'plan_details': plan_selections.get(service_type, {}),
                    'service_details': service_details.get(service_type, {}),
                    'address': confirmation.address_info,
                }
                
                return Response(service_data, status=status.HTTP_200_OK)
                
            except UserOnboardingConfirmation.DoesNotExist:
                return Response(
                    {'error': 'No service information found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"[UserServiceDetailsView] Error fetching service details: {str(e)}")
            return Response(
                {'error': 'Failed to fetch service details'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserServiceInterestView(APIView):
    """
    Manage user interest in upcoming services (mobile, power)
    """
    
    def get(self, request):
        """Get user's current service interests"""
        try:
            # Get authenticated user
            auth_result = UnifiedAuthService.authenticate_user(request)
            
            if not auth_result.is_authenticated:
                return Response(
                    {'error': 'Authentication required', 'details': auth_result.error}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = auth_result.user
            
            # Get or create user preferences
            from core.user_details.models import UserPreferences
            preferences, created = UserPreferences.objects.get_or_create(user=user)
            
            return Response({
                'interested_in_mobile': preferences.interested_in_mobile,
                'interested_in_power': preferences.interested_in_power,
            })
            
        except Exception as e:
            logger.error(f"[UserServiceInterestView] Error fetching service interests: {str(e)}")
            return Response(
                {'error': 'Failed to fetch service interests'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Update user's service interests"""
        try:
            # Get authenticated user
            auth_result = UnifiedAuthService.authenticate_user(request)
            
            if not auth_result.is_authenticated:
                return Response(
                    {'error': 'Authentication required', 'details': auth_result.error}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = auth_result.user
            
            # Handle both JSON and form data
            data = getattr(request, 'data', {})
            if not data:
                import json
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except (json.JSONDecodeError, AttributeError):
                    data = {}
            
            service_type = data.get('service_type')  # 'mobile' or 'power'
            interested = data.get('interested', True)
            
            if service_type not in ['mobile', 'power']:
                return Response(
                    {'error': 'Invalid service type. Must be mobile or power'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user preferences
            from core.user_details.models import UserPreferences
            preferences, created = UserPreferences.objects.get_or_create(user=user)
            
            # Update the specific service interest
            if service_type == 'mobile':
                preferences.interested_in_mobile = interested
            elif service_type == 'power':
                preferences.interested_in_power = interested
                
            preferences.save()
            
            logger.info(f"[UserServiceInterestView] Updated {service_type} interest for user {user.id}: {interested}")
            
            return Response({
                'success': True,
                'service_type': service_type,
                'interested': interested,
                'message': f'Your interest in {service_type} services has been updated'
            })
            
        except Exception as e:
            logger.error(f"[UserServiceInterestView] Error updating service interest: {str(e)}")
            return Response(
                {'error': 'Failed to update service interest'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

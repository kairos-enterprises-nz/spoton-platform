#!/usr/bin/env python3
import os
import sys
import argparse
from decimal import Decimal

# Add the backend directory to Python path (container default)
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
import django

django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from users.models import Tenant, Account, Address, UserAccountRole
from core.user_details.models import UserOnboardingConfirmation, UserPreferences
from users.models import OnboardingProgress
from core.contracts.models import ServiceContract
from energy.connections.models import Connection

User = get_user_model()


def ensure_tenant():
	tenant = Tenant.objects.filter(is_primary_brand=True).first()
	if not tenant:
		tenant = Tenant.objects.create(name='SpotOn Energy', slug='spoton', is_primary_brand=True)
	return tenant


def parse_full_address(full_address: str):
	parts = [p.strip() for p in (full_address or '').split(',') if p.strip()]
	line1 = parts[0] if parts else (full_address or '')
	suburb = parts[1] if len(parts) > 2 else ''
	city = parts[-1] if parts else 'Auckland'
	region = parts[2] if len(parts) > 3 else ''
	return line1, suburb, city, region


@transaction.atomic
def create_test_user(uid: str, email: str = None, full_address: str = None,
					 plan_name: str = 'Fibre Broadband', monthly: float = 79.99,
					 download: str = '100 Mbps', upload: str = '20 Mbps'):
	tenant = ensure_tenant()
	email = email or f"{uid}@example.com"
	full_address = full_address or '1212 Huia Road, Huia, Auckland'

	user, created = User.objects.get_or_create(
		keycloak_id=uid,
		defaults={
			'email': email,
			'first_name': uid.split('-')[0].capitalize(),
			'last_name': uid.split('-')[-1].capitalize(),
			'phone': '+64-21-300-0000',
		}
	)
	if not created:
		user.email = email
		user.first_name = user.first_name or 'Test'
		user.last_name = user.last_name or 'User'
		user.save()

	# Onboarding progress
	progress, _ = OnboardingProgress.objects.get_or_create(user=user)
	progress.current_step = 'completed'
	progress.is_completed = True
	progress.step_data = {
		'aboutYou': {
			'legalFirstName': user.first_name or 'Test',
			'legalLastName': user.last_name or 'User',
			'dob': '1990-01-01',
			'mobile': user.phone or '+64-21-300-0000',
			'email': email,
		},
		'yourServices': {
			'selectedServices': { 'mobile': False, 'broadband': True, 'electricity': False },
			'selectedPlans': {
				'broadband': {
					'id': '101',
					'name': plan_name,
					'rate': monthly,
					'term': '12 Month',
					'charges': { 'monthly_charge': monthly },
					'pricing_id': '00000000-0000-0000-0000-000000000000',
					'description': 'Test broadband plan',
					'upload_speed': upload,
					'download_speed': download,
				},
			},
			'selectedAddress': { 'full_address': full_address },
		},
		'serviceDetails': {
			'data': {
				'completed': True,
				'serviceDetails': {
					'bb_transferType': 'Switch',
					'bb_routerPreference': 'BYO',
					'bb_serviceStartDate': 'asap',
				}
			}
		},
		'preferences': {
			'preferences': { 'billRemindersEmail': True, 'billRemindersSMS': True }
		}
	}
	progress.save()

	# Confirmation snapshot
	about = progress.step_data['aboutYou']
	sel_services = progress.step_data['yourServices']['selectedServices']
	sel_plans = progress.step_data['yourServices']['selectedPlans']
	full_addr = progress.step_data['yourServices']['selectedAddress']['full_address']
	svc_details = progress.step_data['serviceDetails']['data']['serviceDetails']
	prefs = progress.step_data['preferences']['preferences']

	confirmation, _ = UserOnboardingConfirmation.objects.get_or_create(user=user)
	confirmation.address_info = { 'full_address': full_addr, 'broadband_available': True }
	confirmation.services_chosen = sel_services
	confirmation.plan_selections = sel_plans
	confirmation.personal_info = about
	confirmation.service_details = svc_details
	confirmation.payment_info = { 'paymentMethodType': 'BANK_TRANSFER' }
	confirmation.notification_preferences = prefs
	confirmation.is_completed = True
	confirmation.save()

	# Account + role
	role = UserAccountRole.objects.filter(user=user, tenant=tenant).select_related('account').first()
	if role:
		account = role.account
	else:
		account = Account.objects.create(
			tenant=tenant,
			account_type='residential',
			billing_cycle='monthly',
			billing_day=1,
			created_by=user,
		)
		UserAccountRole.objects.create(tenant=tenant, user=user, account=account, role='primary')

	# Address (service)
	line1, suburb, city, region = parse_full_address(full_addr)
	service_address, _ = Address.objects.get_or_create(
		tenant=tenant,
		address_line1=line1,
		city=city,
		postal_code='0000',
		defaults={
			'suburb': suburb,
			'region': region,
			'country': 'New Zealand',
			'address_type': 'service',
			'is_primary': True,
		}
	)
	if account.billing_address is None:
		account.billing_address = service_address
		account.save(update_fields=['billing_address'])

	# Broadband contract
	bb_plan = sel_plans.get('broadband') or {}
	contract = ServiceContract.objects.create(
		tenant=tenant,
		account=account,
		contract_type='broadband',
		service_name=bb_plan.get('name') or 'Broadband Service',
		description='Created from test-user manager',
		start_date=timezone.now(),
		status='pending',
		billing_frequency='monthly',
		base_charge=Decimal(str(bb_plan.get('charges', {}).get('monthly_charge', 0))) if bb_plan else Decimal('0'),
		metadata={
			'plan': bb_plan,
			'transferType': svc_details.get('bb_transferType'),
			'routerPreference': svc_details.get('bb_routerPreference'),
			'serviceStartDate': svc_details.get('bb_serviceStartDate'),
		},
		created_by=user,
		updated_by=user,
	)

	# Connection
	dl = bb_plan.get('download_speed')
	ul = bb_plan.get('upload_speed')
	line_speed = None
	if dl or ul:
		line_speed = f"{(dl or '').replace(' Mbps','')}/{(ul or '').replace(' Mbps','')} Mbps".strip()
	connection = Connection.objects.create(
		tenant=tenant,
		account=account,
		contract_id=contract.id,
		service_address=service_address,
		service_type='broadband',
		ont_serial=f"ONT-{account.account_number}",
		connection_identifier=f"ONT-{account.account_number}",
		status='pending',
		line_speed=line_speed or '',
	)

	# Preferences
	prefs_model, _ = UserPreferences.objects.get_or_create(user=user)
	prefs_model.notification_preferences = prefs
	prefs_model.communication_preferences = {}
	prefs_model.save()

	return {
		'user_id': str(user.id),
		'account_id': str(account.id),
		'service_address_id': str(service_address.id),
		'contract_id': str(contract.id),
		'connection_id': str(connection.id),
	}


@transaction.atomic
def delete_test_user(uid: str):
	# Find user
	try:
		user = User.objects.get(id=uid)
	except User.DoesNotExist:
		return {'deleted': False, 'reason': 'user_not_found'}

	# Delete related onboarding artifacts
	OnboardingProgress.objects.filter(user=user).delete()
	UserOnboardingConfirmation.objects.filter(user=user).delete()
	UserPreferences.objects.filter(user=user).delete()

	# Delete accounts and contracts linked to user via roles
	roles = UserAccountRole.objects.filter(user=user).select_related('account')
	for role in roles:
		account = role.account
		# Delete contracts for account
		ServiceContract.objects.filter(account=account).delete()
		# Delete connections for account
		Connection.objects.filter(account=account).delete()
		# Delete role itself
		role.delete()
		# Finally delete account
		account.delete()

	# Finally delete the user
	user.delete()
	return {'deleted': True}


def main():
	parser = argparse.ArgumentParser(description='Manage test users for UAT')
	subparsers = parser.add_subparsers(dest='command', required=True)

	p_create = subparsers.add_parser('create', help='Create a test user with broadband onboarding completed')
	p_create.add_argument('--uid', required=True, help='Unique user UID (keycloak_id)')
	p_create.add_argument('--email', required=False, help='Email for the user')
	p_create.add_argument('--address', required=False, help='Full address line', default=None)
	p_create.add_argument('--plan-name', required=False, default='Fibre Broadband')
	p_create.add_argument('--monthly', required=False, type=float, default=79.99)
	p_create.add_argument('--download', required=False, default='100 Mbps')
	p_create.add_argument('--upload', required=False, default='20 Mbps')

	p_delete = subparsers.add_parser('delete', help='Delete a test user and related artifacts')
	p_delete.add_argument('--uid', required=True, help='Unique user UID (keycloak_id)')

	args = parser.parse_args()

	if args.command == 'create':
		result = create_test_user(
			uid=args.uid,
			email=args.email,
			full_address=args.address,
			plan_name=args.plan_name,
			monthly=args.monthly,
			download=args.download,
			upload=args.upload,
		)
		print('CREATED', result)
	elif args.command == 'delete':
		result = delete_test_user(uid=args.uid)
		print('DELETED', result)


if __name__ == '__main__':
	main()
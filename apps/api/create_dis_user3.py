#!/usr/bin/env python3
import os
import sys
import uuid
from decimal import Decimal

# Add the backend directory to Python path (container default)
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
import django

django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import Tenant, Account, Address, UserAccountRole
from core.user_details.models import UserOnboardingConfirmation, UserPreferences
from users.models import OnboardingProgress
from core.contracts.models import ServiceContract
from energy.connections.models import Connection

User = get_user_model()


def create_dis_user3():
	print("Creating dis-user-3 with broadband onboarding completed...")

	# 1) Ensure tenant
	tenant = Tenant.objects.filter(is_primary_brand=True).first()
	if not tenant:
		tenant = Tenant.objects.create(name='SpotOn Energy', slug='spoton', is_primary_brand=True)
	print(f"Tenant: {tenant.name} ({tenant.slug})")

	# 2) Create or get user
	keycloak_id = 'dis-user-3'
	email = 'dis.user3@example.com'
	user, created = User.objects.get_or_create(
		keycloak_id=keycloak_id,
		defaults={
			'email': email,
			'first_name': 'Dis',
			'last_name': 'User3',
			'phone': '+64-21-300-0003',
		}
	)
	if not created:
		# Keep data fresh
		user.email = email
		user.first_name = 'Dis'
		user.last_name = 'User3'
		user.phone = '+64-21-300-0003'
		user.save()
	print(f"User: {user.keycloak_id} ({user.email})")

	# 3) Onboarding Progress (completed)
	progress, _ = OnboardingProgress.objects.get_or_create(
		user=user,
		defaults={
			'current_step': 'completed',
			'is_completed': True,
			'step_data': {},
		}
	)
	progress.current_step = 'completed'
	progress.is_completed = True
	progress.step_data = {
		'aboutYou': {
			'legalFirstName': 'Dis',
			'legalLastName': 'User3',
			'dob': '1990-01-01',
			'mobile': '+64-21-300-0003',
			'email': email,
		},
		'yourServices': {
			'selectedServices': { 'mobile': False, 'broadband': True, 'electricity': False },
			'selectedPlans': {
				'broadband': {
					'id': '101',
					'name': 'Fibre Broadband',
					'rate': 79.99,
					'term': '12 Month',
					'charges': { 'monthly_charge': 79.99 },
					'pricing_id': 'e6b9e4fe-d33d-49b0-a194-d614b3576bb8',
					'description': 'Unlimited broadband with fast fibre speeds.',
					'upload_speed': '20 Mbps',
					'download_speed': '100 Mbps',
				},
			},
			'selectedAddress': {
				'full_address': '1212 Huia Road, Huia, Auckland'
			},
		},
		'serviceDetails': {
			'k': 'v',
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
			'preferences': {
				'billRemindersEmail': True,
				'billRemindersSMS': True,
			}
		}
	}
	progress.save()
	print("OnboardingProgress: completed")

	# Extract from progress for consistency
	about = progress.step_data['aboutYou']
	sel_services = progress.step_data['yourServices']['selectedServices']
	sel_plans = progress.step_data['yourServices']['selectedPlans']
	full_address = progress.step_data['yourServices']['selectedAddress']['full_address']
	svc_details = progress.step_data['serviceDetails']['data']['serviceDetails']
	prefs = progress.step_data['preferences']['preferences']

	# 4) Confirmation snapshot
	confirmation, _ = UserOnboardingConfirmation.objects.get_or_create(
		user=user,
		defaults={
			'address_info': { 'full_address': full_address, 'broadband_available': True },
			'services_chosen': sel_services,
			'plan_selections': sel_plans,
			'personal_info': about,
			'service_details': svc_details,
			'payment_info': { 'paymentMethodType': 'BANK_TRANSFER' },
			'notification_preferences': prefs,
			'is_completed': True,
		}
	)
	# Keep it updated if rerun
	confirmation.address_info = { 'full_address': full_address, 'broadband_available': True }
	confirmation.services_chosen = sel_services
	confirmation.plan_selections = sel_plans
	confirmation.personal_info = about
	confirmation.service_details = svc_details
	confirmation.payment_info = { 'paymentMethodType': 'BANK_TRANSFER' }
	confirmation.notification_preferences = prefs
	confirmation.is_completed = True
	confirmation.save()
	print("UserOnboardingConfirmation: saved")

	# 5) Account + role
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
	print(f"Account: {account.account_number}")

	# 6) Address (service) and set as billing if empty
	parts = [p.strip() for p in full_address.split(',') if p.strip()]
	line1 = parts[0] if parts else full_address
	city = parts[-1] if parts else 'Auckland'
	service_address, _ = Address.objects.get_or_create(
		tenant=tenant,
		address_line1=line1,
		city=city,
		postal_code='0000',
		defaults={
			'suburb': parts[1] if len(parts) > 2 else '',
			'region': parts[2] if len(parts) > 3 else '',
			'country': 'New Zealand',
			'address_type': 'service',
			'is_primary': True,
		}
	)
	if account.billing_address is None:
		account.billing_address = service_address
		account.save(update_fields=['billing_address'])
	print(f"Service Address: {service_address}")

	# 7) Broadband contract
	bb_plan = sel_plans.get('broadband') or {}
	contract = ServiceContract.objects.create(
		tenant=tenant,
		account=account,
		contract_type='broadband',
		service_name=bb_plan.get('name') or 'Broadband Service',
		description='Created from script: dis-user-3 onboarding',
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
	print(f"Broadband Contract: {contract.contract_number} ({contract.id})")

	# 8) Connection (broadband)
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
		connection_identifier=f"BB-{account.account_number}",
		status='pending',
		line_speed=line_speed or '',
	)
	print(f"Connection: {connection.id} (identifier={connection.connection_identifier})")

	# 9) Preferences
	prefs_model, _ = UserPreferences.objects.get_or_create(user=user)
	prefs_model.notification_preferences = prefs
	prefs_model.communication_preferences = {}
	prefs_model.save()
	print("UserPreferences: saved")

	# Final summary
	print("\nSummary")
	print("- user_id:", str(user.id))
	print("- account_id:", str(account.id))
	print("- service_address_id:", str(service_address.id))
	print("- contract_id:", str(contract.id))
	print("- connection_id:", str(connection.id))
	print("- onboarding_confirmation:", str(confirmation.id))
	print("- onboarding_progress:", f"completed={progress.is_completed}")

	return {
		'user_id': str(user.id),
		'account_id': str(account.id),
		'service_address_id': str(service_address.id),
		'contract_id': str(contract.id),
		'connection_id': str(connection.id),
	}


if __name__ == '__main__':
	create_dis_user3()
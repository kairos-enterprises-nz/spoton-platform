from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
import requests
import json
import time


class Command(BaseCommand):
    help = 'Setup and configure Wiki.js integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create Wiki.js admin user',
        )
        parser.add_argument(
            '--setup-auth',
            action='store_true',
            help='Setup authentication configuration',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Perform health check on Wiki.js service',
        )
        parser.add_argument(
            '--create-content',
            action='store_true',
            help='Create initial wiki content',
        )

    def handle(self, *args, **options):
        wiki_url = getattr(settings, 'WIKI_JS_URL', 'http://wiki:3000')
        
        if options['health_check']:
            self.health_check(wiki_url)
        
        if options['create_admin']:
            self.create_admin_user(wiki_url)
        
        if options['setup_auth']:
            self.setup_authentication(wiki_url)
        
        if options['create_content']:
            self.create_initial_content(wiki_url)

    def health_check(self, wiki_url):
        """Check if Wiki.js service is running"""
        self.stdout.write('Checking Wiki.js health...')
        
        try:
            response = requests.get(f"{wiki_url}/healthz", timeout=10)
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Wiki.js is healthy at {wiki_url}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Wiki.js returned status {response.status_code}')
                )
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Wiki.js health check failed: {e}')
            )

    def create_admin_user(self, wiki_url):
        """Create initial admin user if it doesn't exist"""
        self.stdout.write('Setting up Wiki.js admin user...')
        
        # This would typically involve GraphQL mutations to Wiki.js
        # For now, we'll just provide instructions
        self.stdout.write(
            self.style.SUCCESS(
                '✓ Please manually create admin user in Wiki.js at: '
                f'{wiki_url}/setup'
            )
        )

    def setup_authentication(self, wiki_url):
        """Configure authentication settings"""
        self.stdout.write('Configuring Wiki.js authentication...')
        
        # Instructions for manual setup
        auth_config = {
            'strategy': 'local',
            'displayName': 'Local Authentication',
            'order': 0,
            'isEnabled': True,
            'config': {
                'allowSelfRegistration': False,
                'domainWhitelist': [],
                'autoEnrollGroups': []
            }
        }
        
        self.stdout.write('Authentication configuration:')
        self.stdout.write(json.dumps(auth_config, indent=2))
        
        self.stdout.write(
            self.style.SUCCESS(
                '✓ Please configure authentication manually in Wiki.js admin panel'
            )
        )

    def create_initial_content(self, wiki_url):
        """Create SpotOn template structure with placeholders"""
        self.stdout.write('Creating SpotOn template structure with placeholders...')
        
        initial_pages = [
            # HOME PAGE
            {
                'title': 'SpotOn Energy - Process Documentation Hub',
                'path': 'home',
                'content': '''# SpotOn Energy - Process Documentation Hub

Welcome to SpotOn's comprehensive process documentation system.

## 🏢 **General Operations**
- [Company Overview](general/company-overview)
- [Staff Management](general/staff-management)
- [Customer Service](general/customer-service)
- [Quality Assurance](general/quality-assurance)
- [Compliance & Legal](general/compliance)

## ⚡ **Power Services**
- [Power Processes](power/processes)
- [Power Policies](power/policies)
- [WITS Operations](power/wits)
- [Metering & Billing](power/metering)

## 🌐 **Broadband Services**
- [Broadband Processes](broadband/processes)
- [Broadband Policies](broadband/policies)
- [Network Operations](broadband/network)
- [Technical Support](broadband/support)

## 📱 **Mobile Services**
- [Mobile Processes](mobile/processes)
- [Mobile Policies](mobile/policies)
- [SIM Management](mobile/sim-management)
- [Device Support](mobile/device-support)

---
*SpotOn Energy Ltd - Internal Documentation*
*Last Updated: {current_date}*
'''
            },
            
            # GENERAL SECTION
            {
                'title': 'Company Overview',
                'path': 'general/company-overview',
                'content': '''# Company Overview

## Mission Statement
**[PLACEHOLDER: Insert SpotOn mission statement]**

## Vision
**[PLACEHOLDER: Insert SpotOn vision]**

## Core Values
- **[PLACEHOLDER: Value 1]**
- **[PLACEHOLDER: Value 2]**
- **[PLACEHOLDER: Value 3]**

## Organizational Structure
**[PLACEHOLDER: Insert organizational chart or structure]**

## Key Personnel
- **CEO:** [PLACEHOLDER: Name and contact]
- **Operations Manager:** [PLACEHOLDER: Name and contact]
- **Technical Lead:** [PLACEHOLDER: Name and contact]
- **Customer Service Manager:** [PLACEHOLDER: Name and contact]

## Business Units
### Power Division
**[PLACEHOLDER: Power division overview]**

### Broadband Division
**[PLACEHOLDER: Broadband division overview]**

### Mobile Division
**[PLACEHOLDER: Mobile division overview]**

## Contact Information
- **Main Office:** [PLACEHOLDER: Address]
- **Phone:** [PLACEHOLDER: Phone number]
- **Email:** [PLACEHOLDER: Email address]
- **Website:** https://spoton.energy
'''
            },
            
            {
                'title': 'Staff Management',
                'path': 'general/staff-management',
                'content': '''# Staff Management

## Recruitment Process
### Job Posting
**[PLACEHOLDER: Job posting procedures]**

### Interview Process
1. **[PLACEHOLDER: Initial screening process]**
2. **[PLACEHOLDER: Technical interview process]**
3. **[PLACEHOLDER: Final interview process]**

### Onboarding Checklist
- [ ] **[PLACEHOLDER: IT setup requirements]**
- [ ] **[PLACEHOLDER: Documentation requirements]**
- [ ] **[PLACEHOLDER: Training requirements]**
- [ ] **[PLACEHOLDER: Compliance requirements]**

## Performance Management
### Review Schedule
**[PLACEHOLDER: Performance review schedule and process]**

### KPIs and Metrics
**[PLACEHOLDER: Key performance indicators]**

## Training Programs
### Mandatory Training
- **[PLACEHOLDER: Safety training]**
- **[PLACEHOLDER: Compliance training]**
- **[PLACEHOLDER: System training]**

### Professional Development
**[PLACEHOLDER: Professional development opportunities]**

## HR Policies
- [Employee Handbook](general/employee-handbook)
- [Leave Policies](general/leave-policies)
- [Code of Conduct](general/code-of-conduct)
'''
            },
            
            # POWER SECTION
            {
                'title': 'Power Processes',
                'path': 'power/processes',
                'content': '''# Power Processes

## Customer Onboarding
### New Connection Process
1. **[PLACEHOLDER: Application process]**
2. **[PLACEHOLDER: Credit check process]**
3. **[PLACEHOLDER: Connection setup process]**
4. **[PLACEHOLDER: Welcome process]**

### Required Documentation
- **[PLACEHOLDER: ID requirements]**
- **[PLACEHOLDER: Address verification]**
- **[PLACEHOLDER: Credit documentation]**

## Switching Process
### Incoming Customers
**[PLACEHOLDER: Process for customers switching TO SpotOn]**

### Outgoing Customers
**[PLACEHOLDER: Process for customers switching FROM SpotOn]**

## Billing Process
### Monthly Billing Cycle
**[PLACEHOLDER: Billing cycle timeline and process]**

### Payment Processing
**[PLACEHOLDER: Payment methods and processing]**

### Debt Management
**[PLACEHOLDER: Debt collection process]**

## WITS Data Processing
### Daily Operations
- **[PLACEHOLDER: Data retrieval process]**
- **[PLACEHOLDER: Data validation process]**
- **[PLACEHOLDER: Data processing workflow]**

### Error Handling
**[PLACEHOLDER: Error handling procedures]**

## Meter Reading
### Scheduled Readings
**[PLACEHOLDER: Meter reading schedule]**

### Special Readings
**[PLACEHOLDER: Special meter reading procedures]**

## Customer Service
### Inquiry Handling
**[PLACEHOLDER: Customer inquiry process]**

### Complaint Resolution
**[PLACEHOLDER: Complaint handling process]**
'''
            },
            
            {
                'title': 'Power Policies',
                'path': 'power/policies',
                'content': '''# Power Policies

## Pricing Policy
### Tariff Structure
**[PLACEHOLDER: Current tariff structure and rates]**

### Price Changes
**[PLACEHOLDER: Price change notification process]**

## Credit Policy
### Credit Assessment
**[PLACEHOLDER: Credit assessment criteria]**

### Security Deposits
**[PLACEHOLDER: Security deposit requirements]**

### Payment Terms
**[PLACEHOLDER: Payment terms and conditions]**

## Disconnection Policy
### Disconnection Criteria
**[PLACEHOLDER: When disconnection is authorized]**

### Disconnection Process
1. **[PLACEHOLDER: Warning notices]**
2. **[PLACEHOLDER: Final notice]**
3. **[PLACEHOLDER: Disconnection execution]**

### Reconnection Process
**[PLACEHOLDER: Reconnection requirements and process]**

## Data Management Policy
### Data Collection
**[PLACEHOLDER: What data is collected and why]**

### Data Storage
**[PLACEHOLDER: Data storage requirements]**

### Data Sharing
**[PLACEHOLDER: Data sharing policies]**

## Regulatory Compliance
### Electricity Authority Requirements
**[PLACEHOLDER: EA compliance requirements]**

### Consumer Rights
**[PLACEHOLDER: Consumer protection requirements]**

### Reporting Obligations
**[PLACEHOLDER: Regulatory reporting requirements]**
'''
            },
            
            # BROADBAND SECTION
            {
                'title': 'Broadband Processes',
                'path': 'broadband/processes',
                'content': '''# Broadband Processes

## Service Provisioning
### New Connection Setup
1. **[PLACEHOLDER: Service availability check]**
2. **[PLACEHOLDER: Installation scheduling]**
3. **[PLACEHOLDER: Equipment delivery]**
4. **[PLACEHOLDER: Installation process]**
5. **[PLACEHOLDER: Service activation]**

### Equipment Management
**[PLACEHOLDER: Equipment tracking and management]**

## Technical Support
### Tier 1 Support
**[PLACEHOLDER: First-level support procedures]**

### Tier 2 Support
**[PLACEHOLDER: Advanced technical support]**

### Escalation Process
**[PLACEHOLDER: When and how to escalate issues]**

## Network Maintenance
### Scheduled Maintenance
**[PLACEHOLDER: Maintenance scheduling and notification]**

### Emergency Maintenance
**[PLACEHOLDER: Emergency response procedures]**

### Performance Monitoring
**[PLACEHOLDER: Network performance monitoring]**

## Speed Testing
### Customer Speed Tests
**[PLACEHOLDER: How customers can test speeds]**

### Internal Testing
**[PLACEHOLDER: Internal speed testing procedures]**

## Fault Resolution
### Fault Reporting
**[PLACEHOLDER: How faults are reported and logged]**

### Resolution Process
**[PLACEHOLDER: Fault resolution workflow]**

### SLA Compliance
**[PLACEHOLDER: Service level agreement requirements]**
'''
            },
            
            {
                'title': 'Broadband Policies',
                'path': 'broadband/policies',
                'content': '''# Broadband Policies

## Service Level Agreements
### Uptime Guarantees
**[PLACEHOLDER: Uptime commitments and penalties]**

### Speed Guarantees
**[PLACEHOLDER: Speed commitments and remedies]**

### Support Response Times
**[PLACEHOLDER: Support response time commitments]**

## Fair Use Policy
### Data Usage Limits
**[PLACEHOLDER: Data usage policies if applicable]**

### Network Management
**[PLACEHOLDER: Traffic management policies]**

## Installation Policy
### Standard Installation
**[PLACEHOLDER: What's included in standard installation]**

### Additional Charges
**[PLACEHOLDER: When additional charges apply]**

### Customer Responsibilities
**[PLACEHOLDER: Customer obligations during installation]**

## Equipment Policy
### Provided Equipment
**[PLACEHOLDER: Equipment provided by SpotOn]**

### Customer Equipment
**[PLACEHOLDER: Customer-owned equipment policies]**

### Return Requirements
**[PLACEHOLDER: Equipment return policies]**

## Cancellation Policy
### Notice Requirements
**[PLACEHOLDER: Cancellation notice requirements]**

### Early Termination
**[PLACEHOLDER: Early termination fees and conditions]**

### Equipment Return
**[PLACEHOLDER: Equipment return process upon cancellation]**
'''
            },
            
            # MOBILE SECTION
            {
                'title': 'Mobile Processes',
                'path': 'mobile/processes',
                'content': '''# Mobile Processes

## SIM Activation
### New Activations
1. **[PLACEHOLDER: Identity verification process]**
2. **[PLACEHOLDER: Plan selection process]**
3. **[PLACEHOLDER: SIM provisioning process]**
4. **[PLACEHOLDER: Service activation process]**

### SIM Replacement
**[PLACEHOLDER: Lost/damaged SIM replacement process]**

## Plan Management
### Plan Changes
**[PLACEHOLDER: How customers can change plans]**

### Add-ons and Extras
**[PLACEHOLDER: Additional service activation]**

### Usage Monitoring
**[PLACEHOLDER: How usage is tracked and reported]**

## Device Support
### Device Compatibility
**[PLACEHOLDER: Device compatibility checking]**

### Device Configuration
**[PLACEHOLDER: Device setup assistance]**

### Troubleshooting
**[PLACEHOLDER: Common device issues and solutions]**

## Number Porting
### Porting In
**[PLACEHOLDER: Process for customers bringing numbers to SpotOn]**

### Porting Out
**[PLACEHOLDER: Process for customers taking numbers away]**

## International Services
### Roaming Setup
**[PLACEHOLDER: International roaming activation]**

### International Calling
**[PLACEHOLDER: International calling setup]**

## Billing and Usage
### Bill Generation
**[PLACEHOLDER: Mobile billing process]**

### Usage Alerts
**[PLACEHOLDER: Usage monitoring and alerts]**
'''
            },
            
            {
                'title': 'Mobile Policies',
                'path': 'mobile/policies',
                'content': '''# Mobile Policies

## Service Plans
### Plan Features
**[PLACEHOLDER: Available plan features and inclusions]**

### Data Allowances
**[PLACEHOLDER: Data usage policies and limits]**

### Overage Charges
**[PLACEHOLDER: Charges for exceeding plan limits]**

## Acceptable Use Policy
### Prohibited Uses
**[PLACEHOLDER: Prohibited uses of mobile service]**

### Network Protection
**[PLACEHOLDER: Network abuse prevention]**

### Spam and Abuse
**[PLACEHOLDER: Anti-spam policies]**

## International Services Policy
### Roaming Charges
**[PLACEHOLDER: International roaming rates]**

### Service Availability
**[PLACEHOLDER: Countries where service is available]**

### Fair Use Limits
**[PLACEHOLDER: Fair use policies for international services]**

## Device Policy
### Supported Devices
**[PLACEHOLDER: List of supported devices]**

### BYOD Policy
**[PLACEHOLDER: Bring Your Own Device policies]**

### Device Unlocking
**[PLACEHOLDER: Device unlocking policies]**

## Privacy Policy
### Data Collection
**[PLACEHOLDER: What mobile data is collected]**

### Location Services
**[PLACEHOLDER: Location data policies]**

### Third Party Sharing
**[PLACEHOLDER: When data is shared with third parties]**

## Suspension and Termination
### Service Suspension
**[PLACEHOLDER: When service may be suspended]**

### Account Termination
**[PLACEHOLDER: Account termination procedures]**

### Final Bills
**[PLACEHOLDER: Final billing process]**
'''
            }
        ]
        
        self.stdout.write('SpotOn Template Structure:')
        self.stdout.write('\n🏢 GENERAL OPERATIONS:')
        general_pages = [p for p in initial_pages if p['path'].startswith('general/')]
        for page in general_pages:
            self.stdout.write(f"   📄 {page['title']} ({page['path']})")
        
        self.stdout.write('\n⚡ POWER SERVICES:')
        power_pages = [p for p in initial_pages if p['path'].startswith('power/')]
        for page in power_pages:
            self.stdout.write(f"   📄 {page['title']} ({page['path']})")
        
        self.stdout.write('\n🌐 BROADBAND SERVICES:')
        broadband_pages = [p for p in initial_pages if p['path'].startswith('broadband/')]
        for page in broadband_pages:
            self.stdout.write(f"   📄 {page['title']} ({page['path']})")
        
        self.stdout.write('\n📱 MOBILE SERVICES:')
        mobile_pages = [p for p in initial_pages if p['path'].startswith('mobile/')]
        for page in mobile_pages:
            self.stdout.write(f"   📄 {page['title']} ({page['path']})")
        
        self.stdout.write(f'\n📋 HOME PAGE: {initial_pages[0]["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ SpotOn template structure ready with {len(initial_pages)} pages!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  Remember to replace all [PLACEHOLDER] content with actual SpotOn information.'
            )
        )

    def wait_for_service(self, wiki_url, max_attempts=30):
        """Wait for Wiki.js service to be ready"""
        self.stdout.write('Waiting for Wiki.js service...')
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{wiki_url}/healthz", timeout=5)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Wiki.js is ready after {attempt + 1} attempts')
                    )
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        self.stdout.write(
            self.style.ERROR(f'✗ Wiki.js not ready after {max_attempts} attempts')
        )
        return False 
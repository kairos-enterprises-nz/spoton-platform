import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model


User = get_user_model()


class Ticket(models.Model):
    """
    Customer support tickets with comprehensive tracking and workflow management
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='support_tickets')
    
    # Ticket identification
    ticket_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Customer information
    customer = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, 
        related_name='support_tickets',
        help_text="Customer who created the ticket"
    )
    account = models.ForeignKey(
        'users.Account', on_delete=models.CASCADE, 
        related_name='support_tickets',
        null=True, blank=True,
        help_text="Customer account (if applicable)"
    )
    connection = models.ForeignKey(
        'connections.Connection', on_delete=models.CASCADE,
        related_name='support_tickets',
        null=True, blank=True,
        help_text="Specific connection/service (if applicable)"
    )
    
    # Ticket classification
    TICKET_TYPE_CHOICES = [
        ('billing', 'Billing Inquiry'),
        ('technical', 'Technical Issue'),
        ('service', 'Service Request'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('connection', 'Connection Issue'),
        ('outage', 'Outage Report'),
        ('meter', 'Meter Reading Issue'),
        ('payment', 'Payment Issue'),
        ('account', 'Account Management'),
        ('general', 'General Inquiry'),
        ('emergency', 'Emergency'),
    ]
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPE_CHOICES)
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Service area
    SERVICE_AREA_CHOICES = [
        ('electricity', 'Electricity'),
        ('broadband', 'Broadband'),
        ('mobile', 'Mobile'),
        ('billing', 'Billing'),
        ('account', 'Account'),
        ('general', 'General'),
    ]
    service_area = models.CharField(max_length=20, choices=SERVICE_AREA_CHOICES, default='general')
    
    # Status and workflow
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('pending_customer', 'Pending Customer Response'),
        ('pending_internal', 'Pending Internal Review'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tickets',
        help_text="Support agent assigned to this ticket"
    )
    assigned_team = models.CharField(
        max_length=50, blank=True,
        help_text="Team or department assigned to handle this ticket"
    )
    
    # Contact information
    contact_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('chat', 'Live Chat'),
            ('portal', 'Customer Portal'),
            ('social', 'Social Media'),
        ],
        default='email'
    )
    contact_details = models.JSONField(
        default=dict,
        help_text="Contact information and preferences"
    )
    
    # Resolution tracking
    resolution = models.TextField(blank=True)
    resolution_category = models.CharField(
        max_length=50, blank=True,
        choices=[
            ('information_provided', 'Information Provided'),
            ('issue_resolved', 'Issue Resolved'),
            ('service_restored', 'Service Restored'),
            ('billing_adjusted', 'Billing Adjusted'),
            ('account_updated', 'Account Updated'),
            ('escalated_external', 'Escalated to External Party'),
            ('no_action_required', 'No Action Required'),
            ('duplicate', 'Duplicate Ticket'),
            ('customer_resolved', 'Customer Self-Resolved'),
        ]
    )
    
    # SLA tracking
    created_at = models.DateTimeField(auto_now_add=True)
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA targets (in hours)
    target_first_response_hours = models.PositiveIntegerField(default=24)
    target_resolution_hours = models.PositiveIntegerField(default=72)
    
    # Customer satisfaction
    customer_rating = models.PositiveIntegerField(
        null=True, blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Customer satisfaction rating (1-5)"
    )
    customer_feedback = models.TextField(blank=True)
    
    # Internal tracking
    internal_notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, help_text="Tags for categorization and search")
    
    # Related tickets
    parent_ticket = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='child_tickets'
    )
    related_tickets = models.ManyToManyField(
        'self', blank=True,
        help_text="Related or duplicate tickets"
    )
    
    # Metadata
    source_channel = models.CharField(
        max_length=50, blank=True,
        help_text="Original channel where ticket was created"
    )
    source_reference = models.CharField(
        max_length=100, blank=True,
        help_text="External reference number or ID"
    )
    
    # Audit fields
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='updated_tickets'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'status', 'priority']),
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['ticket_type', 'service_area']),
            models.Index(fields=['created_at', 'resolved_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_ticket_number():
        """Generate unique ticket number"""
        from django.db.models import Max
        import datetime
        
        today = datetime.date.today()
        prefix = f"TKT{today.strftime('%Y%m%d')}"
        
        last_ticket = Ticket.objects.filter(
            ticket_number__startswith=prefix
        ).aggregate(Max('ticket_number'))['ticket_number__max']
        
        if last_ticket:
            sequence = int(last_ticket[-4:]) + 1
        else:
            sequence = 1
            
        return f"{prefix}{sequence:04d}"
    
    def is_overdue(self):
        """Check if ticket is overdue based on SLA"""
        if self.status in ['resolved', 'closed', 'cancelled']:
            return False
            
        now = timezone.now()
        
        # Check first response SLA
        if not self.first_response_at:
            hours_since_created = (now - self.created_at).total_seconds() / 3600
            if hours_since_created > self.target_first_response_hours:
                return True
        
        # Check resolution SLA
        hours_since_created = (now - self.created_at).total_seconds() / 3600
        if hours_since_created > self.target_resolution_hours:
            return True
            
        return False
    
    def get_age_hours(self):
        """Get ticket age in hours"""
        if self.closed_at:
            end_time = self.closed_at
        else:
            end_time = timezone.now()
        return (end_time - self.created_at).total_seconds() / 3600
    
    def get_resolution_time_hours(self):
        """Get resolution time in hours"""
        if self.resolved_at:
            return (self.resolved_at - self.created_at).total_seconds() / 3600
        return None


class TicketNote(models.Model):
    """
    Internal notes and comments on support tickets
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='notes')
    
    # Note details
    note = models.TextField()
    
    NOTE_TYPE_CHOICES = [
        ('internal', 'Internal Note'),
        ('customer_response', 'Customer Response'),
        ('agent_response', 'Agent Response'),
        ('system', 'System Generated'),
        ('escalation', 'Escalation Note'),
        ('resolution', 'Resolution Note'),
    ]
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='internal')
    
    # Visibility
    is_internal = models.BooleanField(
        default=True,
        help_text="Whether note is visible to customer"
    )
    is_system_generated = models.BooleanField(default=False)
    
    # Author
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ticket_notes'
    )
    
    # Attachments and references
    attachments = models.JSONField(
        default=list,
        help_text="List of file attachments"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['note_type', 'is_internal']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_number} - Note by {self.created_by} ({self.note_type})"


class CallLog(models.Model):
    """
    Phone support call logging with duration and recording information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='call_logs')
    
    # Associated ticket (optional)
    ticket = models.ForeignKey(
        'Ticket', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='call_logs'
    )
    
    # Call details
    call_id = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20)
    
    # Customer information
    customer = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='call_logs'
    )
    customer_name = models.CharField(max_length=200, blank=True)
    
    # Call handling
    agent = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='handled_calls'
    )
    
    CALL_TYPE_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('callback', 'Callback'),
        ('transfer', 'Transfer'),
    ]
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    
    CALL_STATUS_CHOICES = [
        ('answered', 'Answered'),
        ('missed', 'Missed'),
        ('busy', 'Busy'),
        ('no_answer', 'No Answer'),
        ('voicemail', 'Voicemail'),
        ('dropped', 'Dropped'),
    ]
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES)
    
    # Timing
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    
    # Call content
    purpose = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    
    # Recording information
    recording_url = models.URLField(blank=True)
    recording_duration = models.PositiveIntegerField(
        default=0,
        help_text="Recording duration in seconds"
    )
    has_recording = models.BooleanField(default=False)
    
    # Quality and compliance
    call_quality_score = models.PositiveIntegerField(
        null=True, blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Call quality rating (1-5)"
    )
    compliance_reviewed = models.BooleanField(default=False)
    compliance_notes = models.TextField(blank=True)
    
    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateTimeField(null=True, blank=True)
    followup_notes = models.TextField(blank=True)
    
    # System integration
    phone_system_id = models.CharField(max_length=100, blank=True)
    external_references = models.JSONField(
        default=dict,
        help_text="External system references and metadata"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'started_at']),
            models.Index(fields=['customer', 'call_type']),
            models.Index(fields=['agent', 'started_at']),
            models.Index(fields=['phone_number', 'started_at']),
            models.Index(fields=['ticket']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.call_id} - {self.phone_number} ({self.call_type}, {self.duration_seconds}s)"
    
    def save(self, *args, **kwargs):
        # Calculate duration if not set
        if self.started_at and self.ended_at and self.duration_seconds == 0:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
        super().save(*args, **kwargs)
    
    def get_duration_formatted(self):
        """Get formatted duration string"""
        if self.duration_seconds == 0:
            return "0:00"
        
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"


class SupportKnowledgeBase(models.Model):
    """
    Knowledge base articles for support agents and customers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE, related_name='knowledge_articles')
    
    # Article details
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    # Categorization
    CATEGORY_CHOICES = [
        ('billing', 'Billing'),
        ('technical', 'Technical'),
        ('account', 'Account Management'),
        ('service', 'Service Information'),
        ('troubleshooting', 'Troubleshooting'),
        ('policy', 'Policies & Procedures'),
        ('faq', 'Frequently Asked Questions'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    tags = models.JSONField(default=list)
    keywords = models.TextField(blank=True, help_text="Search keywords")
    
    # Audience
    AUDIENCE_CHOICES = [
        ('internal', 'Internal (Agents Only)'),
        ('customer', 'Customer Facing'),
        ('both', 'Both Internal and Customer'),
    ]
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='internal')
    
    # Status and workflow
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Versioning
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='newer_versions'
    )
    
    # Usage tracking
    view_count = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    unhelpful_votes = models.PositiveIntegerField(default=0)
    
    # Content management
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='authored_articles'
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_articles'
    )
    
    # Dates
    published_at = models.DateTimeField(null=True, blank=True)
    review_due_date = models.DateField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'category', 'status']),
            models.Index(fields=['audience', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['published_at']),
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title} ({self.category})"
    
    def get_helpfulness_ratio(self):
        """Calculate helpfulness ratio"""
        total_votes = self.helpful_votes + self.unhelpful_votes
        if total_votes == 0:
            return 0
        return (self.helpful_votes / total_votes) * 100
    
    def is_due_for_review(self):
        """Check if article is due for review"""
        if not self.review_due_date:
            return False
        return timezone.now().date() >= self.review_due_date 
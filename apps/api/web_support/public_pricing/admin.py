from django.contrib import admin
from .models import ElectricityPlan, BroadbandPlan, PricingRegion, MobilePlan


@admin.register(ElectricityPlan)
class ElectricityPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'name', 'plan_type', 'city', 'base_rate', 'is_active', 'updated_at']
    list_filter = ['plan_type', 'city', 'is_active', 'term']
    search_fields = ['name', 'city', 'description']
    readonly_fields = ['pricing_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pricing_id', 'plan_id', 'name', 'plan_type', 'description', 'term', 'terms_url')
        }),
        ('Geographic', {
            'fields': ('city',)
        }),
        ('Base Pricing', {
            'fields': ('base_rate', 'rate_details')
        }),
        ('Standard User Charges', {
            'fields': ('standard_daily_charge', 'standard_variable_charge')
        }),
        ('Low User Charges', {
            'fields': ('low_user_daily_charge', 'low_user_variable_charge')
        }),
        ('Time-based Charges (TOU Plans)', {
            'fields': ('peak_charge', 'off_peak_charge', 'low_user_peak_charge', 'low_user_off_peak_charge'),
            'classes': ('collapse',)
        }),
        ('Spot Pricing Charges', {
            'fields': ('wholesale_rate', 'network_charge'),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(BroadbandPlan)
class BroadbandPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'name', 'plan_type', 'city', 'monthly_charge', 'is_active', 'updated_at']
    list_filter = ['plan_type', 'city', 'is_active', 'term']
    search_fields = ['name', 'city', 'description']
    readonly_fields = ['pricing_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pricing_id', 'plan_id', 'name', 'plan_type', 'description', 'term', 'terms_url')
        }),
        ('Geographic', {
            'fields': ('city',)
        }),
        ('Pricing', {
            'fields': ('base_rate', 'rate_details', 'monthly_charge', 'setup_fee')
        }),
        ('Service Specifications', {
            'fields': ('data_allowance', 'download_speed', 'upload_speed')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(PricingRegion)
class PricingRegionAdmin(admin.ModelAdmin):
    list_display = ['city', 'display_name', 'service_availability', 'is_active', 'updated_at']
    list_filter = ['service_availability', 'is_active']
    search_fields = ['city', 'display_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Region Information', {
            'fields': ('city', 'display_name', 'service_availability', 'is_active')
        }),
        ('Geographic Coordinates (Optional)', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MobilePlan)
class MobilePlanAdmin(admin.ModelAdmin):
    list_display = ['plan_id', 'name', 'plan_type', 'city', 'monthly_charge', 'data_allowance', 'is_active', 'updated_at']
    list_filter = ['plan_type', 'city', 'is_active', 'term']
    search_fields = ['name', 'city', 'description']
    readonly_fields = ['pricing_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'plan_type', 'description', 'term', 'terms_url')
        }),
        ('Pricing', {
            'fields': ('base_rate', 'rate_details', 'monthly_charge', 'setup_fee', 'sim_card_fee')
        }),
        ('Plan Features', {
            'fields': ('data_allowance', 'minutes', 'texts')
        }),
        ('Availability', {
            'fields': ('city', 'is_active')
        }),
        ('System Information', {
            'fields': ('pricing_id', 'plan_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

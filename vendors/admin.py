from django.contrib import admin
from django.utils.html import format_html
from .models import Vendor, VendorKYC, VendorPayout


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'user', 'business_email', 'kyc_status', 'is_active', 'created_at']
    list_filter = ['kyc_status', 'is_active', 'created_at']
    search_fields = ['store_name', 'business_email', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'store_name', 'store_logo', 'store_banner')
        }),
        ('Business Details', {
            'fields': ('business_email', 'business_phone', 'store_description', 'store_address')
        }),
        ('Status & Settings', {
            'fields': ('kyc_status', 'kyc_rejection_reason', 'is_active', 'commission_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(VendorKYC)
class VendorKYCAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'verification_status', 'submitted_at', 'verified_by', 'verified_at']
    list_filter = ['verification_status', 'submitted_at', 'verified_at']
    search_fields = ['vendor__store_name', 'bank_account_holder']
    readonly_fields = ['submitted_at']
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor',)
        }),
        ('Documents', {
            'fields': ('pan_document', 'gstin_document')
        }),
        ('Bank Details', {
            'fields': ('bank_account_number', 'bank_ifsc', 'bank_account_holder')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if change and obj.verification_status == 'verified' and not obj.verified_by:
            obj.verified_by = request.user
            from django.utils import timezone
            obj.verified_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'amount', 'status', 'requested_at', 'processed_by', 'processed_at']
    list_filter = ['status', 'requested_at', 'processed_at']
    search_fields = ['vendor__store_name', 'transaction_reference']
    readonly_fields = ['requested_at']
    
    fieldsets = (
        ('Payout Information', {
            'fields': ('vendor', 'amount', 'orders_included', 'bank_details')
        }),
        ('Status', {
            'fields': ('status', 'transaction_reference')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('requested_at',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if change and obj.status == 'processed' and not obj.processed_by:
            obj.processed_by = request.user
            from django.utils import timezone
            obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)

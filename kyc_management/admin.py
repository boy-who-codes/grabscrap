from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import KYCApproval, KYCNotification

@admin.register(KYCApproval)
class KYCApprovalAdmin(admin.ModelAdmin):
    list_display = [
        'vendor_email', 'vendor_name', 'store_name', 'status', 
        'submitted_at', 'reviewed_at', 'admin_user'
    ]
    list_filter = ['status', 'submitted_at', 'reviewed_at']
    search_fields = ['vendor_profile__user__email', 'vendor_profile__user__full_name', 'vendor_profile__store_name']
    readonly_fields = ['vendor_profile', 'submitted_at', 'reviewed_at']
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor_profile', 'vendor_details')
        }),
        ('KYC Documents', {
            'fields': ('pan_details', 'gstin_details', 'address_details')
        }),
        ('Approval Decision', {
            'fields': ('status', 'rejection_reason', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'reviewed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vendor_email(self, obj):
        return obj.vendor_profile.user.email
    vendor_email.short_description = 'Vendor Email'
    
    def vendor_name(self, obj):
        return obj.vendor_profile.user.full_name
    vendor_name.short_description = 'Vendor Name'
    
    def store_name(self, obj):
        return obj.vendor_profile.store_name
    store_name.short_description = 'Store Name'
    
    def vendor_details(self, obj):
        user = obj.vendor_profile.user
        return format_html(
            '<strong>Name:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Phone:</strong> {}<br>'
            '<strong>Business Email:</strong> {}<br>'
            '<strong>Business Phone:</strong> {}',
            user.full_name,
            user.email,
            user.mobile_number or 'Not provided',
            obj.vendor_profile.business_email,
            obj.vendor_profile.business_phone or 'Not provided'
        )
    vendor_details.short_description = 'Vendor Details'
    
    def pan_details(self, obj):
        kyc = obj.vendor_profile.kyc
        pan_doc = f'<a href="{kyc.pan_document.url}" target="_blank">View PAN Document</a>' if kyc.pan_document else 'No document uploaded'
        return format_html(
            '<strong>PAN Number:</strong> {}<br>'
            '<strong>PAN Document:</strong> {}',
            obj.vendor_profile.pan or 'Not provided',
            mark_safe(pan_doc)
        )
    pan_details.short_description = 'PAN Details'
    
    def gstin_details(self, obj):
        kyc = obj.vendor_profile.kyc
        gstin_doc = f'<a href="{kyc.gstin_document.url}" target="_blank">View GSTIN Document</a>' if kyc.gstin_document else 'No document uploaded'
        return format_html(
            '<strong>GSTIN Number:</strong> {}<br>'
            '<strong>GSTIN Document:</strong> {}',
            obj.vendor_profile.gstin or 'Not provided',
            mark_safe(gstin_doc)
        )
    gstin_details.short_description = 'GSTIN Details'
    
    def address_details(self, obj):
        address = obj.vendor_profile.store_address or {}
        return format_html(
            '<strong>Address Line 1:</strong> {}<br>'
            '<strong>Address Line 2:</strong> {}<br>'
            '<strong>City:</strong> {}<br>'
            '<strong>State:</strong> {}<br>'
            '<strong>Pincode:</strong> {}<br>'
            '<strong>Coordinates:</strong> {}, {}',
            address.get('line1', 'Not provided'),
            address.get('line2', 'Not provided'),
            address.get('city', 'Not provided'),
            address.get('state', 'Not provided'),
            address.get('pincode', 'Not provided'),
            address.get('latitude', 'Not provided'),
            address.get('longitude', 'Not provided')
        )
    address_details.short_description = 'Store Address'
    
    def save_model(self, request, obj, instance):
        if not obj.admin_user_id:
            obj.admin_user = request.user
        super().save_model(request, obj, instance)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'vendor_profile__user', 'vendor_profile__kyc', 'admin_user'
        )

@admin.register(KYCNotification)
class KYCNotificationAdmin(admin.ModelAdmin):
    list_display = ['vendor_email', 'notification_type', 'sent_at', 'sent_successfully']
    list_filter = ['notification_type', 'sent_successfully', 'sent_at']
    search_fields = ['vendor__email', 'vendor__full_name']
    readonly_fields = ['vendor', 'kyc_approval', 'sent_at']
    
    def vendor_email(self, obj):
        return obj.vendor.email
    vendor_email.short_description = 'Vendor Email'

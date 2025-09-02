from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'coupon_type', 'vendor', 'used_count', 'usage_limit', 'is_active', 'valid_until']
    list_filter = ['coupon_type', 'discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'name', 'vendor__store_name']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value', 'max_discount', 'min_order_amount')
        }),
        ('Coupon Type', {
            'fields': ('coupon_type', 'vendor', 'created_by')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'used_count', 'user_limit')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Vendors can only see their own coupons
        if hasattr(request.user, 'vendor_profile'):
            return qs.filter(vendor=request.user.vendor_profile)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new coupon
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'discount_amount', 'created_at']
    list_filter = ['coupon__coupon_type', 'created_at']
    search_fields = ['coupon__code', 'user__username', 'order__order_number']
    readonly_fields = ['created_at']

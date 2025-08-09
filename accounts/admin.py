from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, VendorProfile, VendorKYC, Wallet, WalletTransaction

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'mobile_number', 'profile_photo', 'user_type', 'is_verified', 'is_phone_verified', 'email_verified_at', 'is_banned')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
        }),
    )
    list_display = ('email', 'username', 'full_name', 'user_type', 'is_active', 'is_verified', 'is_phone_verified', 'is_banned', 'is_staff')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('email',)

class AddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'city', 'user', 'address_type', 'is_default')
    search_fields = ('recipient_name', 'city', 'user__email')
    list_filter = ('address_type', 'city', 'is_default')

class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'kyc_status', 'is_active')
    search_fields = ('store_name', 'user__email', 'business_email')
    list_filter = ('kyc_status', 'is_active')

class VendorKYCAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'verification_status', 'verified_by', 'verified_at', 'submitted_at')
    search_fields = ('vendor__store_name',)
    list_filter = ('verification_status',)

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_balance', 'held_amount', 'is_active')
    search_fields = ('user__email',)
    list_filter = ('is_active',)

class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'status', 'created_at')
    search_fields = ('wallet__user__email', 'transaction_type')
    list_filter = ('transaction_type', 'status')

admin.site.register(User, UserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(VendorProfile, VendorProfileAdmin)
admin.site.register(VendorKYC, VendorKYCAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin) 
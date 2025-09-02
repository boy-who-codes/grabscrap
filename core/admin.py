from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, Category, SystemSettings, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'full_name', 'user_type', 'is_verified', 'is_banned', 'date_joined')
    list_filter = ('is_verified', 'is_banned', 'user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'full_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'mobile_number', 'profile_photo', 'user_type', 'is_verified', 'is_banned')
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'user', 'city', 'address_type', 'is_default')
    list_filter = ('address_type', 'is_default', 'city', 'state')
    search_fields = ('recipient_name', 'user__email', 'city')
    ordering = ('-is_default', '-created_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'description')
    ordering = ('key',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

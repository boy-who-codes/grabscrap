from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Cart, CartItem, Order, OrderItem, Payment, 
    OrderStatusHistory, ShippingMethod, OrderTracking
)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['product', 'quantity', 'total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_amount', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__full_name', 'user__email']
    readonly_fields = ['total_items', 'total_amount']
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_items', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['product', 'quantity', 'unit_price', 'total_price', 'product_title']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['transaction_id', 'created_at']
    fields = ['payment_method', 'amount', 'status', 'transaction_id']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['changed_by', 'created_at']
    fields = ['status', 'changed_by', 'notes', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'vendor', 'status', 'payment_status', 
        'total_amount', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at', 'vendor__store_name'
    ]
    search_fields = [
        'order_number', 'user__full_name', 'user__email', 
        'vendor__store_name'
    ]
    readonly_fields = [
        'order_number', 'subtotal', 'tax_amount', 'shipping_fee', 
        'commission_amount', 'total_amount', 'created_at', 'updated_at'
    ]
    inlines = [OrderItemInline, PaymentInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'vendor', 'order_number', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_fee', 'commission_amount', 'total_amount')
        }),
        ('Addresses', {
            'fields': ('billing_address', 'shipping_address'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'vendor_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'vendor')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_title', 'quantity', 'unit_price', 'total_price']
    search_fields = ['order__order_number', 'product_title', 'product_sku']
    readonly_fields = ['total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'payment_method', 'amount', 'status', 
        'transaction_id', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = [
        'order__order_number', 'transaction_id', 'order__user__full_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'payment_method', 'amount', 'status')
        }),
        ('Gateway Details', {
            'fields': ('transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'changed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'changed_by__full_name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'changed_by')


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_fee', 'estimated_days', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['base_fee', 'estimated_days', 'is_active']


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['order', 'tracking_number', 'carrier', 'status', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['order__order_number', 'tracking_number', 'carrier']
    readonly_fields = ['timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')

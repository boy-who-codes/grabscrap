from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, Payment, Refund


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product_snapshot',)
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'vendor', 'total_amount', 'order_status', 'payment_status', 'created_at')
    list_filter = ('order_status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__username', 'vendor__store_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'updated_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'escrow_status', 'held_at')
    list_filter = ('payment_method', 'escrow_status', 'held_at')
    search_fields = ('order__order_number',)


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'status', 'requested_by', 'processed_by')
    list_filter = ('status', 'processed_at')
    search_fields = ('order__order_number', 'reason')

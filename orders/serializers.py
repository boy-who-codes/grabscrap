from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, Payment, Refund
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.store_name', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'order_number', 'user', 'vendor', 'payment_status', 'escrow_status']


class OrderCreateSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField()
    delivery_address_id = serializers.UUIDField()
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'
        read_only_fields = ['id', 'order', 'updated_by']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'order', 'held_at', 'released_at', 'released_by']


class RefundSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = ['id', 'order', 'requested_by', 'processed_by', 'processed_at']

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from accounts.models import User, VendorProfile, Address
from products.models import Product


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"

    def __str__(self):
        return f"Cart for {self.user.full_name}"

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_weight(self):
        return sum(item.total_weight for item in self.items.all())


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.quantity}x {self.product.title} in {self.cart}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    @property
    def total_weight(self):
        # Assuming weight is stored in product specifications or calculated
        # For now, return 0 - can be enhanced later
        return 0

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity < self.product.minimum_order_quantity:
            raise ValidationError(
                f'Minimum order quantity for {self.product.title} is {self.product.minimum_order_quantity}'
            )
        if self.quantity > self.product.stock_quantity:
            raise ValidationError(
                f'Only {self.product.stock_quantity} units available for {self.product.title}'
            )


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('wallet', 'Wallet'),
        ('cod', 'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Addresses
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    customer_notes = models.TextField(blank=True)
    vendor_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order {self.order_number} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-YYYYMMDD-XXXXX
            import random
            import string
            date_prefix = timezone.now().strftime('%Y%m%d')
            random_suffix = ''.join(random.choice(string.digits) for _ in range(5))
            self.order_number = f"ORD-{date_prefix}-{random_suffix}"
        super().save(*args, **kwargs)

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def can_cancel(self):
        return self.status in ['pending', 'confirmed']

    @property
    def can_refund(self):
        return self.status in ['delivered'] and self.payment_status == 'paid'

    def calculate_totals(self):
        """Calculate order totals including tax, shipping, and commission"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        
        # Calculate tax (example: 18% GST)
        self.tax_amount = self.subtotal * Decimal('0.18')
        
        # Calculate shipping fee (example: based on weight or fixed)
        self.shipping_fee = Decimal('50.00')  # Fixed shipping for now
        
        # Calculate commission (example: 5% of subtotal)
        commission_rate = self.vendor.category.commission_rate if self.vendor.category.commission_rate else Decimal('5.00')
        self.commission_amount = self.subtotal * (commission_rate / Decimal('100'))
        
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_fee
        self.save()


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product snapshot at time of order
    product_title = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    product_unit = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.product_title} in {self.order}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('wallet', 'Wallet'),
        ('razorpay', 'Razorpay'),
        ('paytm', 'Paytm'),
        ('cod', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment gateway details
    transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment {self.transaction_id or self.id} - {self.order.order_number}"

    @property
    def is_successful(self):
        return self.status == 'completed'

    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled']


class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.created_at}"


class ShippingMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery time in days")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Shipping Method"
        verbose_name_plural = "Shipping Methods"

    def __str__(self):
        return self.name


class OrderTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Tracking"

    def __str__(self):
        return f"Tracking for {self.order.order_number} - {self.status}"

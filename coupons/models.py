from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import BaseModel
import uuid

User = get_user_model()


class Coupon(BaseModel):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    COUPON_TYPES = [
        ('global', 'Global (Admin)'),
        ('vendor', 'Vendor Specific'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Discount details
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Coupon type and ownership
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    user_limit = models.PositiveIntegerField(default=1)  # Per user limit
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def can_use(self, user, order_amount):
        if not self.is_valid:
            return False, "Coupon is not valid"
        
        if order_amount < self.min_order_amount:
            return False, f"Minimum order amount is ₹{self.min_order_amount}"
        
        # Check user usage limit
        user_usage = CouponUsage.objects.filter(coupon=self, user=user).count()
        if user_usage >= self.user_limit:
            return False, "You have already used this coupon"
        
        return True, "Valid"

    def calculate_discount(self, order_amount):
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value
        
        return min(discount, order_amount)


class CouponUsage(BaseModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['coupon', 'order']

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.username}"

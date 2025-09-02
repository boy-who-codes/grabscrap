from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel

User = get_user_model()


class Wallet(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_recharged = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    held_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - ₹{self.current_balance}"


class WalletTransaction(BaseModel):
    TRANSACTION_TYPES = [
        ('recharge', 'Recharge'),
        ('hold', 'Hold'),
        ('deduct', 'Deduct'),
        ('release', 'Release'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.UUIDField(blank=True, null=True)
    payment_gateway_ref = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField()
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - ₹{self.amount}"

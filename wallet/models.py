from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

TRANSACTION_TYPES = (
    ('credit', 'Credit'),
    ('debit', 'Debit'),
)

TRANSACTION_STATUS = (
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
)

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet"

    def get_balance(self):
        return self.balance

    def deposit(self, amount, description='Deposit'):
        """Add money to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        self.balance += amount
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            status='completed',
            description=description
        )
        return self.balance

    def withdraw(self, amount, description='Withdrawal'):
        """Deduct money from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        self.balance -= amount
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='debit',
            status='completed',
            description=description
        )
        return self.balance


class Transaction(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(blank=True, null=True)
    reference_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.reference_id:
            # Generate a unique reference ID
            import uuid
            self.reference_id = f"TXN{str(uuid.uuid4().int)[:15]}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

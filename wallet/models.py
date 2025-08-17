from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
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

class WalletManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user__user_type='buyer')
    
    def get_or_create_for_buyer(self, user, **kwargs):
        """Get or create a wallet, but only for buyers"""
        if user.user_type != 'buyer':
            raise ValueError("Wallets can only be created for buyers")
        wallet, created = self.get_or_create(user=user, **kwargs)
        return wallet, created


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_wallet',
        limit_choices_to={'user_type': 'buyer'},
        help_text='Only buyers can have wallets'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this wallet is active.'
    )

    objects = WalletManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
        permissions = [
            ('can_view_wallet', 'Can view wallet'),
            ('can_manage_wallet', 'Can manage wallet'),
            ('add_money', 'Can add money to wallet'),
            ('withdraw_money', 'Can withdraw money from wallet'),
        ]

    def __str__(self):
        return f"{self.user.email}'s Buyer Wallet"

    def clean(self):
        """Ensure only buyers can have wallets"""
        if self.user.user_type != 'buyer':
            raise ValidationError('Wallets can only be created for buyers')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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

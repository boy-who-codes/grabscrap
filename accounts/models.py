import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

ADDRESS_TYPE_CHOICES = [
    ('home', 'Home'),
    ('office', 'Office'),
    ('other', 'Other'),
]
KYC_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, full_name='', mobile_number='', **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Auto-generate a unique username
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user = self.model(email=email, username=username, full_name=full_name, mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, full_name='', mobile_number='', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, full_name, mobile_number, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True, default=None)
    password_history = models.JSONField(default=list, blank=True)
    is_banned = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    user_type = models.CharField(max_length=10, choices=[('buyer', 'Buyer'), ('vendor', 'Vendor'), ('admin', 'Admin')], default='buyer')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    flat_number = models.CharField(max_length=100, blank=True)
    street_address = models.TextField()
    landmark = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=100, help_text='Locality/Area name')
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'

    def save(self, *args, **kwargs):
        # If this address is being set as default, unset default for other addresses
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(id=self.id).update(is_default=False)
        # If this is the user's first address, make it default
        elif not self.id and not Address.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.recipient_name} - {self.city}"

class VendorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    locations = models.ManyToManyField('products.Location', related_name='vendors', blank=True)
    store_name = models.CharField(max_length=255, unique=True)
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    store_banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    store_description = models.TextField(blank=True)
    store_address = models.JSONField(blank=True, null=True)
    business_hours = models.JSONField(blank=True, null=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='pending')
    kyc_rejection_reason = models.TextField(blank=True)
    kyc_approved_at = models.DateTimeField(blank=True, null=True, default=None)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pan = models.CharField(max_length=20, blank=True, null=True)
    gstin = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.store_name

class VendorKYC(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.OneToOneField(VendorProfile, on_delete=models.CASCADE, related_name='kyc')
    pan_document = models.FileField(upload_to='kyc/pan/', blank=True, null=True)
    gstin_document = models.FileField(upload_to='kyc/gstin/', blank=True, null=True)
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=20, blank=True, null=True)
    bank_account_holder = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending')
    verified_by = models.UUIDField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True, default=None)
    rejection_reason = models.TextField(blank=True, null=True, default=None)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KYC for {self.vendor.store_name}"

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='accounts_wallet',
        limit_choices_to={'user_type': 'buyer'}  # Only allow buyers to have wallets
    )
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_recharged = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    held_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Buyer Wallet'
        verbose_name_plural = 'Buyer Wallets'

    def save(self, *args, **kwargs):
        # Ensure only buyers can have wallets
        if self.user.user_type != 'buyer':
            raise ValueError("Wallets can only be created for buyers")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Wallet of {self.user.email} (Buyer)"

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('recharge', 'Recharge via Razorpay'),
        ('hold', 'Hold Amount for Order'),
        ('deduct', 'Deduct on Delivery'),
        ('refund', 'Refund to Wallet'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.UUIDField(blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    balance_before = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.status})"

class OTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

class PhoneOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_otps')
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at
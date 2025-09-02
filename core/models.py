from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """Base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class User(AbstractUser):
    """Custom User model with additional fields"""
    USER_TYPES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    mobile_number = models.CharField(
        max_length=20, 
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='customer'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    @property
    def is_vendor(self):
        return hasattr(self, 'vendor_profile') and self.vendor_profile is not None
    
    @property
    def is_admin_user(self):
        return self.is_staff or self.is_superuser
    
    def get_user_type_display(self):
        if self.is_admin_user:
            return 'Admin'
        elif self.is_vendor:
            return 'Vendor'
        return 'Customer'


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Order Update'),
        ('payment', 'Payment'),
        ('chat', 'New Message'),
        ('system', 'System'),
        ('vendor', 'Vendor Update'),
        ('admin', 'Admin Notice'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict, blank=True)  # Additional data like order_id, etc.
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='system', data=None):
        """Create a new notification and keep only latest 15"""
        # Create new notification
        notification = cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {}
        )
        
        # Keep only latest 15 notifications per user
        user_notifications = cls.objects.filter(user=user).order_by('-created_at')
        if user_notifications.count() > 15:
            old_notifications = user_notifications[15:]
            cls.objects.filter(id__in=[n.id for n in old_notifications]).delete()
        
        return notification


class SystemSettings(BaseModel):
    """System-wide settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class Category(BaseModel):
    """Product categories"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Address(BaseModel):
    """User addresses"""
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='home')
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20)
    flat_number = models.CharField(max_length=100, blank=True)
    street_address = models.TextField()
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.recipient_name} - {self.address_type}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset all other default addresses for this user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        parts = [
            self.flat_number,
            self.street_address,
            self.landmark,
            self.city,
            f"{self.state} - {self.pincode}",
            self.country
        ]
        return ", ".join([part for part in parts if part])

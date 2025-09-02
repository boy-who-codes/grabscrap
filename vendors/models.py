from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel

User = get_user_model()


class Vendor(BaseModel):
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    store_name = models.CharField(max_length=255, unique=True)
    store_logo = models.ImageField(upload_to='vendors/logos/', blank=True, null=True)
    store_banner = models.ImageField(upload_to='vendors/banners/', blank=True, null=True)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=20)
    store_description = models.TextField(blank=True)
    store_address = models.JSONField()
    business_hours = models.JSONField(blank=True, null=True)
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='pending')
    kyc_rejection_reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return self.store_name
    
    def can_sell(self):
        """Check if vendor can sell products"""
        return self.kyc_status == 'approved' and self.is_active
    
    @property
    def is_kyc_approved(self):
        return self.kyc_status == 'approved'


class VendorKYC(BaseModel):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name='kyc_documents')
    pan_document = models.FileField(upload_to='vendors/kyc/pan/')
    gstin_document = models.FileField(upload_to='vendors/kyc/gstin/')
    bank_account_number = models.CharField(max_length=50)
    bank_ifsc = models.CharField(max_length=20)
    bank_account_holder = models.CharField(max_length=255)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='verified_kycs')
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.vendor.store_name} - KYC"


class VendorPayout(BaseModel):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    orders_included = models.JSONField()
    bank_details = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    transaction_reference = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.vendor.store_name} - ₹{self.amount}"

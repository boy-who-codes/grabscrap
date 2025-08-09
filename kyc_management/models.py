from django.db import models
from django.utils import timezone
from accounts.models import User, VendorProfile

class KYCApproval(models.Model):
    """Model to track KYC approval decisions by admin"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='kyc_approvals')
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_approvals_given')
    
    # Bank account details
    bank_account_holder = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Name of the account holder as per bank records"
    )
    bank_account_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Bank account number"
    )
    bank_ifsc = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="IFSC code of the bank branch"
    )
    
    # Approval details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection if status is 'rejected'")
    
    # Document verification
    is_document_verified = models.BooleanField(default=False, help_text="Whether documents were properly verified")
    document_verification_notes = models.TextField(blank=True, null=True, help_text="Notes about document verification")
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin reference")
    
    @property
    def can_reapply(self):
        """Check if vendor can reapply for KYC"""
        return self.status == 'rejected' and self.reviewed_at and \
               (timezone.now() - self.reviewed_at).days >= 7
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "KYC Approval"
        verbose_name_plural = "KYC Approvals"
    
    def __str__(self):
        return f"KYC Approval for {self.vendor_profile.user.email} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Update reviewed_at when status changes from pending
        if self.pk:  # If this is an update
            old_instance = KYCApproval.objects.get(pk=self.pk)
            if old_instance.status == 'pending' and self.status != 'pending':
                self.reviewed_at = timezone.now()
        elif self.status != 'pending':  # If this is a new instance with non-pending status
            self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update vendor profile KYC status
        if self.status in ['approved', 'rejected']:
            self.vendor_profile.kyc_status = self.status
            if self.status == 'approved':
                self.vendor_profile.kyc_approved_at = timezone.now()
            self.vendor_profile.save()

class KYCNotification(models.Model):
    """Model to track KYC status notifications sent to vendors"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both'),
    ]
    
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_notifications')
    kyc_approval = models.ForeignKey(KYCApproval, on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_successfully = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "KYC Notification"
        verbose_name_plural = "KYC Notifications"
    
    def __str__(self):
        return f"KYC Notification to {self.vendor.email} - {self.notification_type}"

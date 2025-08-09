from django import forms
from django.core.validators import FileExtensionValidator
from .models import KYCApproval

class VendorKYCForm(forms.ModelForm):
    pan_document = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Upload PAN card (PDF, JPG, JPEG, or PNG)'
    )
    gstin_document = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Upload GSTIN certificate (PDF, JPG, JPEG, or PNG)'
    )
    bank_account_proof = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Upload bank account proof (PDF, JPG, JPEG, or PNG)'
    )
    
    class Meta:
        model = KYCApproval
        fields = ['pan_document', 'gstin_document', 'bank_account_proof', 'bank_account_number', 'bank_ifsc', 'bank_account_holder']
        widgets = {
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_ifsc': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account_holder': forms.TextInput(attrs={'class': 'form-control'}),
        }

class KYCReviewForm(forms.ModelForm):
    class Meta:
        model = KYCApproval
        fields = ['status', 'rejection_reason', 'admin_notes', 'is_document_verified', 'document_verification_notes']
        widgets = {
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document_verification_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

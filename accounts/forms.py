from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.models import Address

User = get_user_model()


class UnifiedSignupForm(UserCreationForm):
    """Unified signup form for customers, vendors, and admins"""
    
    user_type = forms.ChoiceField(
        choices=User.USER_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='customer',
        label='Account Type'
    )
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email address'
    }))
    full_name = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your full name'
    }))
    mobile_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your mobile number'
    }))
    store_name = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your store/business name (for vendors)'
    }))
    
    class Meta:
        model = User
        fields = ('user_type', 'email', 'full_name', 'mobile_number', 'store_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists")
        return email
    
    def clean_store_name(self):
        user_type = self.cleaned_data.get('user_type')
        store_name = self.cleaned_data.get('store_name')
        
        if user_type == 'vendor' and not store_name:
            raise ValidationError("Store name is required for vendor accounts")
        
        return store_name
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.full_name = self.cleaned_data['full_name']
        user.mobile_number = self.cleaned_data['mobile_number']
        user.user_type = self.cleaned_data['user_type']
        user.username = self.cleaned_data['email']  # Use email as username
        
        if commit:
            user.save()
            
            # Create vendor profile if vendor
            if self.cleaned_data['user_type'] == 'vendor':
                from vendors.models import Vendor
                Vendor.objects.create(
                    user=user,
                    store_name=self.cleaned_data['store_name'],
                    business_email=user.email,
                    business_phone=user.mobile_number,
                    store_address={},  # Will be updated later in vendor profile
                    kyc_status='pending'
                )
        
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
        'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            try:
                user = User.objects.get(email=username)
                if user.is_banned:
                    raise ValidationError("Your account has been suspended.")
                # Remove email verification check from form - handle in view
            except User.DoesNotExist:
                pass
        
        return super().clean()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('full_name', 'mobile_number', 'profile_photo')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_type', 'recipient_name', 'recipient_phone', 'flat_number',
                 'street_address', 'landmark', 'city', 'state', 'pincode', 'is_default')
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'flat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'street_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

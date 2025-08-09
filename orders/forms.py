from django import forms
from django.core.exceptions import ValidationError
from .models import CartItem, Order, Payment, ShippingMethod
from accounts.models import Address
from .models import Order


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'min': 1,
                'placeholder': 'Quantity'
            })
        }

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if self.product:
            self.fields['quantity'].widget.attrs['max'] = self.product.stock_quantity
            self.fields['quantity'].widget.attrs['min'] = self.product.minimum_order_quantity

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.product:
            if quantity < self.product.minimum_order_quantity:
                raise ValidationError(
                    f'Minimum order quantity for {self.product.title} is {self.product.minimum_order_quantity}'
                )
            if quantity > self.product.stock_quantity:
                raise ValidationError(
                    f'Only {self.product.stock_quantity} units available for {self.product.title}'
                )
        return quantity


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['billing_address', 'shipping_address', 'customer_notes']
        widgets = {
            'billing_address': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'shipping_address': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'customer_notes': forms.Textarea(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'rows': 3,
                'placeholder': 'Any special instructions for your order...'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['billing_address'].queryset = Address.objects.filter(user=self.user)
            self.fields['shipping_address'].queryset = Address.objects.filter(user=self.user)

    def clean(self):
        cleaned_data = super().clean()
        billing_address = cleaned_data.get('billing_address')
        shipping_address = cleaned_data.get('shipping_address')
        
        if not billing_address:
            raise ValidationError('Billing address is required.')
        
        if not shipping_address:
            raise ValidationError('Shipping address is required.')
        
        return cleaned_data


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # Filter payment methods based on user wallet balance
        if self.user and self.order:
            wallet_balance = getattr(self.user.wallet, 'current_balance', 0)
            if wallet_balance < self.order.total_amount:
                # Remove wallet option if insufficient balance
                choices = list(self.fields['payment_method'].choices)
                choices = [choice for choice in choices if choice[0] != 'wallet']
                self.fields['payment_method'].choices = choices


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'address_type', 'recipient_name', 'recipient_phone', 
            'flat_number', 'street_address', 'landmark', 
            'city', 'pincode', 'state', 'country'
        ]
        widgets = {
            'address_type': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Full Name'
            }),
            'recipient_phone': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Phone Number',
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]*'
            }),
            'flat_number': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Flat/House Number'
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Street Address'
            }),
            'landmark': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Landmark (Optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'City'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Pincode',
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]*'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'State'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Country'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode and len(pincode) != 6:
            raise ValidationError('Pincode must be 6 digits.')
        return pincode

    def clean_recipient_phone(self):
        phone = self.cleaned_data.get('recipient_phone')
        if phone and len(phone) < 10:
            raise ValidationError('Phone number must be at least 10 digits.')
        return phone


class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'rows': 3,
            'placeholder': 'Add notes about this status change...'
        }),
        required=False
    )


class OrderSearchForm(forms.Form):
    order_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'placeholder': 'Search by order number...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    payment_status = forms.ChoiceField(
        choices=[('', 'All Payment Statuses')] + Order.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'type': 'date'
        })
    )


class VendorOrderFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    payment_status = forms.ChoiceField(
        choices=[('', 'All Payment Statuses')] + Order.PAYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'type': 'date'
        })
    ) 


class CheckoutForm(forms.ModelForm):
    shipping_address = forms.CharField(widget=forms.Textarea)
    payment_method = forms.ChoiceField(choices=Order.PAYMENT_CHOICES)
    
    class Meta:
        model = Order
        fields = ['shipping_address', 'payment_method']
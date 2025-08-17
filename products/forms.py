from django import forms
from django.core.exceptions import ValidationError
from .models import Category, Product, ProductImage, ProductReview, Location


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent_category', 'icon', 'is_active', 'sort_order', 'commission_rate']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'parent_category': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'icon': forms.FileInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'min': 0
            }),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'step': '0.01',
                'min': 0,
                'max': 100,
                'placeholder': 'Enter commission rate (%)'
            })
        }

    def clean_commission_rate(self):
        commission_rate = self.cleaned_data.get('commission_rate')
        if commission_rate is not None and (commission_rate < 0 or commission_rate > 100):
            raise ValidationError('Commission rate must be between 0 and 100 percent.')
        return commission_rate


class ProductForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'accept': 'image/*'
        }),
        required=False,
        help_text="Upload an image (you can add more images after creating the product)"
    )

    class Meta:
        model = Product
        fields = [
            'category', 'title', 'description', 'price', 'unit', 
            'stock_quantity', 'minimum_order_quantity', 'is_active', 
            'is_featured', 'tags', 'specifications', 'available_locations'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter product title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'rows': 4,
                'placeholder': 'Enter detailed product description'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'step': '0.01',
                'min': 0,
                'placeholder': 'Enter price'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'min': 0,
                'placeholder': 'Enter stock quantity'
            }),
            'minimum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'min': 1,
                'placeholder': 'Enter minimum order quantity'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter tags separated by commas'
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'rows': 3,
                'placeholder': 'Enter specifications as JSON (optional)'
            }),
            'available_locations': forms.SelectMultiple(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            })
        }

    def __init__(self, *args, **kwargs):
        self.vendor = kwargs.pop('vendor', None)
        super().__init__(*args, **kwargs)
        # Only show active categories and locations
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['available_locations'].queryset = Location.objects.filter(is_active=True)

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise ValidationError('Price must be greater than zero.')
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock_quantity

    def clean_minimum_order_quantity(self):
        min_order = self.cleaned_data.get('minimum_order_quantity')
        if min_order < 1:
            raise ValidationError('Minimum order quantity must be at least 1.')
        return min_order

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            # Convert comma-separated string to list
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            return tag_list
        return []

    def clean_specifications(self):
        specs = self.cleaned_data.get('specifications')
        if specs:
            try:
                import json
                # Try to parse as JSON if it's a string
                if isinstance(specs, str):
                    json.loads(specs)
                return specs
            except json.JSONDecodeError:
                raise ValidationError('Specifications must be valid JSON format.')
        return {}


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'sort_order']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'accept': 'image/*'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter alt text for accessibility'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'min': 0
            })
        }


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter review title'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'rows': 4,
                'placeholder': 'Write your review here...'
            })
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise ValidationError('Rating must be between 1 and 5.')
        return rating


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'city', 'state', 'country', 'latitude', 'longitude', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter location name'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter state/province'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'placeholder': 'Enter country'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'step': '0.000001',
                'placeholder': 'Enter latitude'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control text-white',
                'style': 'background:#18181C; color:#fff;',
                'step': '0.000001',
                'placeholder': 'Enter longitude'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        
        if latitude is not None and (latitude < -90 or latitude > 90):
            self.add_error('latitude', 'Latitude must be between -90 and 90 degrees')
        
        if longitude is not None and (longitude < -180 or longitude > 180):
            self.add_error('longitude', 'Longitude must be between -180 and 180 degrees')
        
        return cleaned_data


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'placeholder': 'Search products...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'placeholder': 'Min price'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;',
            'placeholder': 'Max price'
        })
    )
    unit = forms.ChoiceField(
        choices=[('', 'All Units')] + Product.UNIT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control text-white',
            'style': 'background:#18181C; color:#fff;'
        })
    )
    in_stock_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
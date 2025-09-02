from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Web URLs
    path('dashboard/', views.vendor_dashboard, name='dashboard'),
    path('register-form/', views.vendor_register_form, name='register_form'),
    path('kyc-form/', views.vendor_kyc_form, name='kyc_form'),
    path('orders/', views.vendor_orders, name='orders'),
    path('products/', views.vendor_products, name='products'),
    path('payouts/', views.vendor_payouts, name='payouts'),
    
    # API URLs
    path('api/register/', views.vendor_registration, name='register'),
    path('api/profile/', views.VendorProfileView.as_view(), name='profile'),
    path('api/kyc/', views.VendorKYCView.as_view(), name='kyc'),
    path('api/payouts/', views.VendorPayoutListView.as_view(), name='payout_list'),
    path('api/analytics/', views.vendor_analytics, name='analytics'),
]

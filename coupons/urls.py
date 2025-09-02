from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('validate/', views.validate_coupon, name='validate'),
    path('vendor/', views.vendor_coupons, name='vendor_list'),
    path('vendor/create/', views.create_vendor_coupon, name='vendor_create'),
]

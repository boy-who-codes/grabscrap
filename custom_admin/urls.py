from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/analytics/', views.user_analytics, name='user_analytics'),
    path('users/toggle-ban/<uuid:user_id>/', views.toggle_user_ban, name='toggle_user_ban'),
    
    # KYC Management
    path('kyc/', views.kyc_verification, name='kyc_verification'),
    path('kyc/approve/<uuid:vendor_id>/', views.approve_kyc, name='approve_kyc'),
    path('kyc/reject/<uuid:vendor_id>/', views.reject_kyc, name='reject_kyc'),
    
    # Chat Moderation
    path('chat-moderation/', views.chat_moderation, name='chat_moderation'),
    path('moderate-message/<uuid:message_id>/', views.moderate_message, name='moderate_message'),
    
    # Commission Management
    path('commission/', views.commission_management, name='commission_management'),
    
    # Coupon Management
    path('coupons/', views.coupon_management, name='coupon_management'),
    
    # Advertisement Management
    path('advertisements/', views.advertisement_management, name='advertisement_management'),
    
    # Escrow Management
    path('escrow/', views.escrow_management, name='escrow_management'),
    path('escrow/release/<uuid:order_id>/', views.release_escrow, name='release_escrow'),
    path('escrow/dispute/<uuid:order_id>/', views.dispute_escrow, name='dispute_escrow'),
]

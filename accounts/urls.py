from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # Auth and registration
    path('signup/', views.signup, name='signup'),
    path('confirmation-mail-sent/', views.confirmation_mail_sent, name='confirmation_mail_sent'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Email activation
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('resend-activation/', views.resend_activation, name='resend_activation'),
    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    # 2FA/OTP
    path('otp/', views.otp_verify, name='otp_verify'),
    # Phone verification
    path('phone-verify/', views.phone_verify, name='phone_verify'),
    path('send_phone_otp/', views.send_phone_otp, name='send_phone_otp'),
    path('verify_phone_otp/', views.verify_phone_otp, name='verify_phone_otp'),
    # Profile
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    # Wallet
    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('wallet/recharge/', views.wallet_recharge, name='wallet_recharge'),

]
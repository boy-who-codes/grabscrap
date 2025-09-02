from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    
    # Password Reset
    path('password-reset/', PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/password-reset-complete/'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Admin Actions
    path('admin/update-kyc/', views.admin_update_kyc, name='admin_update_kyc'),
    path('admin/moderate-message/', views.admin_moderate_message, name='admin_moderate_message'),
    
    # Profile & Address Management
    path('profile/', views.profile, name='profile'),
    path('addresses/', views.addresses, name='addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/<uuid:address_id>/edit/', views.edit_address, name='edit_address'),
    path('addresses/<uuid:address_id>/delete/', views.delete_address, name='delete_address'),
    path('addresses/<uuid:address_id>/set-default/', views.set_default_address, name='set_default_address'),
]

from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Template views
    path('', views.wallet_detail, name='detail'),
    path('recharge/', views.recharge_wallet, name='recharge'),
    path('transactions/', views.transaction_history, name='transactions'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('payment-error/', views.payment_error_log, name='payment_error_log'),
]

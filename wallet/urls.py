from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Template views
    path('', views.wallet_detail, name='detail'),
    path('recharge/', views.recharge_wallet, name='recharge'),
    path('transactions/', views.transaction_history, name='transactions'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    
    # API endpoints
    path('api/', views.WalletDetailView.as_view(), name='api_detail'),
    path('api/transactions/', views.WalletTransactionListView.as_view(), name='api_transactions'),
    path('api/recharge/', views.api_recharge_wallet, name='api_recharge'),
]

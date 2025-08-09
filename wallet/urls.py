from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('', views.WalletDetailView.as_view(), name='detail'),
    path('add-money/', views.add_money, name='add_money'),
    path('withdraw/', views.request_withdrawal, name='withdraw'),
    path('transactions/', views.transaction_history, name='transactions'),
]

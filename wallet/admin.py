from django.contrib import admin
from .models import Wallet, Transaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'wallet', 'amount', 'transaction_type', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('reference_id', 'wallet__user__email', 'description')
    readonly_fields = ('reference_id', 'created_at', 'updated_at')
    list_select_related = ('wallet__user',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wallet__user')

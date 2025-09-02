from rest_framework import serializers
from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'current_balance', 'total_recharged', 'total_spent', 'held_amount', 'is_active']
        read_only_fields = ['id', 'total_recharged', 'total_spent']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = '__all__'
        read_only_fields = ['id', 'wallet', 'balance_before', 'balance_after', 'processed_at']


class WalletRechargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=100, max_value=50000)
    payment_method = serializers.ChoiceField(choices=['upi', 'card', 'netbanking'])
    
    def validate_amount(self, value):
        if value < 100:
            raise serializers.ValidationError("Minimum recharge amount is ₹100")
        if value > 50000:
            raise serializers.ValidationError("Maximum recharge amount is ₹50,000")
        return value

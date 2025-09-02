from celery import shared_task
from django.db import transaction
from .models import WalletTransaction, Wallet
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_wallet_recharge(transaction_id, payment_method):
    """Process wallet recharge payment"""
    try:
        wallet_transaction = WalletTransaction.objects.get(id=transaction_id)
        wallet = wallet_transaction.wallet
        
        # Simulate payment gateway processing
        # In real implementation, integrate with Razorpay/Stripe
        payment_success = True  # Simulate success
        
        if payment_success:
            with transaction.atomic():
                # Update wallet balance
                wallet.current_balance += wallet_transaction.amount
                wallet.total_recharged += wallet_transaction.amount
                wallet.save()
                
                # Update transaction
                wallet_transaction.status = 'completed'
                wallet_transaction.balance_after = wallet.current_balance
                wallet_transaction.payment_gateway_ref = f"PAY_{transaction_id[:8]}"
                wallet_transaction.save()
                
                logger.info(f"Wallet recharge successful: {transaction_id}")
                return f"Recharge successful: ₹{wallet_transaction.amount}"
        else:
            wallet_transaction.status = 'failed'
            wallet_transaction.save()
            logger.error(f"Wallet recharge failed: {transaction_id}")
            return f"Recharge failed: {transaction_id}"
            
    except Exception as e:
        logger.error(f"Error processing wallet recharge: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def release_held_amount(order_id):
    """Release held amount after order completion"""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        wallet = order.user.wallet
        
        # Find hold transaction
        hold_transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order_id=order_id,
            transaction_type='hold',
            status='completed'
        ).first()
        
        if hold_transaction:
            with transaction.atomic():
                # Release held amount and deduct from wallet
                wallet.held_amount -= hold_transaction.amount
                wallet.total_spent += hold_transaction.amount
                wallet.save()
                
                # Create deduct transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='deduct',
                    amount=hold_transaction.amount,
                    order_id=order_id,
                    description=f'Payment for order {order.order_number}',
                    balance_before=wallet.current_balance,
                    balance_after=wallet.current_balance,
                    status='completed'
                )
                
                logger.info(f"Amount released for order: {order_id}")
                return f"Amount released for order: {order.order_number}"
                
    except Exception as e:
        logger.error(f"Error releasing held amount: {str(e)}")
        return f"Error: {str(e)}"

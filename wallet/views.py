from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer, WalletRechargeSerializer
from .tasks import process_wallet_recharge
import razorpay
import json
import hmac
import hashlib


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_key'),
    getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret')
))


@login_required
def wallet_detail(request):
    """Wallet detail view - only for customers"""
    # Redirect vendors to their dashboard
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "Wallet is not available for vendors.")
        return redirect('vendors:dashboard')
    
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'transactions': page_obj,
    }
    return render(request, 'wallet/detail.html', context)


@login_required
def recharge_wallet(request):
    """Wallet recharge with Razorpay integration"""
    # Redirect vendors
    if hasattr(request.user, 'vendor_profile'):
        messages.error(request, "Wallet recharge is not available for vendors.")
        return redirect('vendors:dashboard')
    
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            
            if amount < 100:
                messages.error(request, 'Minimum recharge amount is ₹100')
                return render(request, 'wallet/recharge.html', {'wallet': wallet})
            
            if amount > 50000:
                messages.error(request, 'Maximum recharge amount is ₹50,000')
                return render(request, 'wallet/recharge.html', {'wallet': wallet})
            
            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                'amount': int(amount * 100),  # Amount in paise
                'currency': 'INR',
                'payment_capture': 1
            })
            
            # Create pending transaction
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='recharge',
                amount=amount,
                payment_gateway_ref=razorpay_order['id'],
                status='pending',
                description=f'Wallet recharge of ₹{amount}',
                balance_before=wallet.current_balance,
                balance_after=wallet.current_balance
            )
            
            context = {
                'wallet': wallet,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_key'),
                'amount': amount,
                'transaction_id': transaction.id,
                'user_name': request.user.full_name or request.user.username,
                'user_email': request.user.email,
                'user_phone': request.user.mobile_number or '',
            }
            
            return render(request, 'wallet/payment.html', context)
            
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
    
    context = {
        'wallet': wallet,
        'recent_recharges': WalletTransaction.objects.filter(
            wallet=wallet,
            transaction_type='recharge',
            status='completed'
        ).order_by('-created_at')[:5]
    }
    
    return render(request, 'wallet/recharge.html', context)


@login_required
def transaction_history(request):
    """Detailed transaction history"""
    # Redirect vendors
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "Transaction history is not available for vendors.")
        return redirect('vendors:dashboard')
    
    wallet = get_object_or_404(Wallet, user=request.user)
    
    # Filter transactions
    transaction_type = request.GET.get('type', 'all')
    transactions = WalletTransaction.objects.filter(wallet=wallet)
    
    if transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)
    
    transactions = transactions.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'transactions': page_obj,
        'transaction_type': transaction_type,
    }
    
    return render(request, 'wallet/transactions.html', context)


@csrf_exempt
@require_POST
def payment_callback(request):
    """Handle Razorpay payment callback"""
    try:
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        transaction_id = request.POST.get('transaction_id')
        
        # Verify payment signature
        generated_signature = hmac.new(
            getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret').encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature == razorpay_signature:
            # Payment successful
            transaction = get_object_or_404(WalletTransaction, id=transaction_id)
            
            # Update transaction
            transaction.status = 'completed'
            transaction.payment_gateway_ref = razorpay_payment_id
            transaction.save()
            
            # Update wallet balance
            wallet = transaction.wallet
            wallet.current_balance += transaction.amount
            wallet.total_recharged += transaction.amount
            transaction.balance_after = wallet.current_balance
            wallet.save()
            transaction.save()
            
            messages.success(request, f'Wallet recharged successfully with ₹{transaction.amount}!')
            return redirect('wallet:detail')
        else:
            # Payment verification failed
            transaction = get_object_or_404(WalletTransaction, id=transaction_id)
            transaction.status = 'failed'
            transaction.save()
            
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('wallet:recharge')
            
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('wallet:recharge')


# API Views
class WalletDetailView(generics.RetrieveAPIView):
    """Get wallet details"""
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class WalletTransactionListView(generics.ListAPIView):
    """Get wallet transactions"""
    serializer_class = WalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_recharge_wallet(request):
    """API endpoint for wallet recharge"""
    serializer = WalletRechargeSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Create transaction record
        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='recharge',
            amount=amount,
            status='pending',
            description=f'Wallet recharge via {payment_method}',
            metadata={'payment_method': payment_method}
        )
        
        # Process payment asynchronously
        process_wallet_recharge.delay(str(transaction.id))
        
        return Response({
            'message': 'Recharge initiated successfully',
            'transaction_id': transaction.id,
            'amount': amount,
            'status': 'pending'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

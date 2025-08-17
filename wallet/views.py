import logging
from django.shortcuts import render, redirect, get_object_or_404, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from decimal import Decimal
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ValidationError

from .models import Wallet, Transaction

# Set up logging
logger = logging.getLogger(__name__)


def buyer_required(view_func=None, login_url='accounts:login'):
    """
    Decorator to ensure the user is a buyer.
    """
    def test_func(user):
        return user.is_authenticated and user.user_type == 'buyer'
    
    if view_func:
        return user_passes_test(test_func, login_url=login_url)(view_func)
    return user_passes_test(test_func, login_url=login_url)


class BuyerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only buyers can access the view."""
    login_url = 'accounts:login'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'buyer'
    
    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            messages.error(self.request, 'This section is only available for buyers.')
            return redirect('home:index')
        return super().handle_no_permission()


@method_decorator(login_required, name='dispatch')
class WalletDetailView(BuyerRequiredMixin, DetailView):
    model = Wallet
    template_name = 'wallet/detail.html'
    context_object_name = 'wallet'
    
    def get_object(self, queryset=None):
        """Get or create wallet for the current buyer user"""
        try:
            # Get or create wallet using WalletManager (only for buyers)
            wallet, created = Wallet.objects.get_or_create_for_buyer(
                user=self.request.user,
                defaults={'balance': 0}
            )
            return wallet
        except Exception as e:
            logger.error(f"Error getting wallet for user {self.request.user.id}: {str(e)}")
            raise Http404("Wallet not found")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            wallet = self.get_object()
            transactions = wallet.transactions.all().order_by('-created_at')
            
            # Pagination
            paginator = Paginator(transactions, 10)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            # Calculate totals
            credit_total = wallet.transactions.filter(
                transaction_type='credit',
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            debit_total = wallet.transactions.filter(
                transaction_type='debit',
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            context.update({
                'transactions': page_obj,
                'total_credit': credit_total,
                'total_debit': debit_total,
                'net_balance': credit_total - debit_total
            })
            
        except Exception as e:
            logger.error(f"Error in WalletDetailView: {str(e)}")
            messages.error(self.request, 'An error occurred while loading wallet details')
            
        return context


@login_required
@buyer_required
def add_money(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            
            # Get or create wallet using WalletManager (only for buyers)
            wallet, created = Wallet.objects.get_or_create_for_buyer(
                user=request.user,
                defaults={'balance': 0}
            )
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('wallet:detail')
                
            wallet.deposit(amount, 'Wallet top up')
            messages.success(request, f'Successfully added ₹{amount} to your wallet')
            
        except (ValueError, TypeError) as e:
            messages.error(request, 'Please enter a valid amount')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    return redirect('wallet:detail')


@login_required
@buyer_required
def request_withdrawal(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            
            # Get wallet using WalletManager (only for buyers)
            try:
                wallet = Wallet.objects.get(user=request.user)
            except Wallet.DoesNotExist:
                messages.error(request, 'Wallet not found')
                return redirect('wallet:detail')
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('wallet:detail')
                
            wallet.withdraw(amount, 'Withdrawal request')
            messages.success(request, f'Withdrawal request for ₹{amount} has been submitted')
            
        except ValueError as e:
            messages.error(request, str(e))
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    return redirect('wallet:detail')


@login_required
@buyer_required
def transaction_history(request):
    try:
        # Get wallet using WalletManager (only for buyers)
        wallet = Wallet.objects.get(user=request.user)
        transactions = wallet.transactions.all().order_by('-created_at')
        
        # Filtering
        transaction_type = request.GET.get('type')
        if transaction_type in ['credit', 'debit']:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        # Search
        search_query = request.GET.get('q')
        if search_query:
            transactions = transactions.filter(
                Q(description__icontains=search_query) |
                Q(reference_id__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(transactions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'wallet': wallet,
            'transactions': page_obj,
            'transaction_type': transaction_type or '',
            'search_query': search_query or '',
        }
        
        return render(request, 'wallet/transaction_history.html', context)
        
    except Wallet.DoesNotExist:
        messages.error(request, 'Wallet not found')
        return redirect('home:index')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('home:index')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from decimal import Decimal

from .models import Wallet, Transaction


@method_decorator(login_required, name='dispatch')
class WalletDetailView(DetailView):
    model = Wallet
    template_name = 'wallet/detail.html'
    context_object_name = 'wallet'
    
    def get_object(self, queryset=None):
        # Get or create wallet for the current user
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = self.object.transactions.all().order_by('-created_at')
        
        # Pagination
        paginator = Paginator(transactions, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['transactions'] = page_obj
        context['total_credit'] = self.object.transactions.filter(
            transaction_type='credit',
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        context['total_debit'] = self.object.transactions.filter(
            transaction_type='debit',
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        return context


@login_required
def add_money(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            wallet = Wallet.objects.get_or_create(user=request.user)[0]
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('wallet:detail')
                
            wallet.deposit(amount, 'Wallet top up')
            messages.success(request, f'Successfully added ₹{amount} to your wallet')
            
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    return redirect('wallet:detail')


@login_required
def request_withdrawal(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            wallet = Wallet.objects.get(user=request.user)
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('wallet:detail')
                
            wallet.withdraw(amount, 'Withdrawal request')
            messages.success(request, f'Withdrawal request for ₹{amount} has been submitted')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Wallet.DoesNotExist:
            messages.error(request, 'Wallet not found')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    return redirect('wallet:detail')


@login_required
def transaction_history(request):
    wallet = get_object_or_404(Wallet, user=request.user)
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
            Q(reference_id__iexact=search_query)
        )
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'transaction_type': transaction_type,
        'search_query': search_query or '',
    }
    
    return render(request, 'wallet/transaction_history.html', context)

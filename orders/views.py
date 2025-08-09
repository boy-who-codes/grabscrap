from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from accounts.models import User, VendorProfile, Address, Wallet, WalletTransaction
from products.models import Product
from .models import Cart, CartItem, Order, OrderItem, Payment, OrderStatusHistory, ShippingMethod, OrderTracking
from .forms import (
    CartItemForm, OrderForm, PaymentForm, AddressForm, 
    OrderStatusUpdateForm, OrderSearchForm, VendorOrderFilterForm, CheckoutForm
)
import uuid



@login_required
def cart_view(request):
    """Display user's shopping cart"""
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'is_active': True}
    )
    
    cart_items = cart.items.select_related('product', 'product__vendor').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    
    return render(request, 'orders/cart.html', context)


@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    if not product.can_order:
        messages.error(request, 'This product is not available for ordering.')
        return redirect('products:product_detail', product_id=product_id)
    
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'is_active': True}
    )
    
    form = CartItemForm(request.POST, product=product)
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'{product.title} added to cart!')
    else:
        messages.error(request, form.errors['quantity'][0])
    
    return redirect('orders:cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    form = CartItemForm(request.POST, product=cart_item.product, instance=cart_item)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cart updated successfully!')
    else:
        messages.error(request, form.errors['quantity'][0])
    
    return redirect('orders:cart')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_title = cart_item.product.title
    cart_item.delete()
    
    messages.success(request, f'{product_title} removed from cart!')
    return redirect('orders:cart')


@login_required
def checkout(request):
    """Checkout process"""
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    cart_items = cart.items.select_related('product', 'product__vendor').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('orders:cart')
    
    # Group items by vendor
    vendor_items = {}
    for item in cart_items:
        vendor = item.product.vendor
        if vendor not in vendor_items:
            vendor_items[vendor] = []
        vendor_items[vendor].append(item)
    
    if request.method == 'POST':
        order_form = OrderForm(request.POST, user=request.user)
        payment_form = PaymentForm(request.POST, user=request.user)
        
        if order_form.is_valid() and payment_form.is_valid():
            # Process checkout for each vendor
            orders_created = []
            
            for vendor, items in vendor_items.items():
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        vendor=vendor,
                        billing_address=order_form.cleaned_data['billing_address'],
                        shipping_address=order_form.cleaned_data['shipping_address'],
                        customer_notes=order_form.cleaned_data['customer_notes'],
                        subtotal=0,
                        total_amount=0
                    )
                    
                    # Create order items
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            unit_price=item.product.price,
                            total_price=item.total_price,
                            product_title=item.product.title,
                            product_sku=item.product.sku,
                            product_unit=item.product.unit
                        )
                        
                        # Update product stock
                        item.product.stock_quantity -= item.quantity
                        item.product.save()
                    
                    # Calculate order totals
                    order.calculate_totals()
                    
                    # Create payment
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=payment_form.cleaned_data['payment_method'],
                        amount=order.total_amount
                    )
                    
                    orders_created.append(order)
            
            # Clear cart
            cart.is_active = False
            cart.save()
            
            # Redirect to payment or order confirmation
            if len(orders_created) == 1:
                return redirect('orders:process_payment', order_id=orders_created[0].id)
            else:
                return redirect('orders:order_list')
    
    else:
        order_form = OrderForm(user=request.user)
        payment_form = PaymentForm(user=request.user)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'vendor_items': vendor_items,
        'order_form': order_form,
        'payment_form': payment_form,
    }
    
    return render(request, 'orders/checkout.html', context)


@login_required
def process_payment(request, order_id):
    """Process payment for an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid.')
        return redirect('orders:order_detail', order_id=order.id)
    
    payment = order.payments.first()
    
    if request.method == 'POST':
        if payment.payment_method == 'wallet':
            # Process wallet payment
            wallet = request.user.wallet
            if wallet.current_balance >= order.total_amount:
                with transaction.atomic():
                    # Deduct from wallet
                    wallet.current_balance -= order.total_amount
                    wallet.total_spent += order.total_amount
                    wallet.save()
                    
                    # Create wallet transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='debit',
                        amount=order.total_amount,
                        order_id=order.order_number,
                        status='completed',
                        description=f'Payment for order {order.order_number}',
                        balance_before=wallet.current_balance + order.total_amount,
                        balance_after=wallet.current_balance
                    )
                    
                    # Update payment status
                    payment.status = 'completed'
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    # Update order status
                    order.payment_status = 'paid'
                    order.status = 'confirmed'
                    order.confirmed_at = timezone.now()
                    order.save()
                    
                    # Create status history
                    OrderStatusHistory.objects.create(
                        order=order,
                        status='confirmed',
                        changed_by=request.user,
                        notes='Payment completed via wallet'
                    )
                    
                    messages.success(request, 'Payment completed successfully!')
                    return redirect('orders:order_detail', order_id=order.id)
            else:
                messages.error(request, 'Insufficient wallet balance.')
        else:
            # Redirect to external payment gateway
            # This would integrate with Razorpay, Paytm, etc.
            messages.info(request, 'Redirecting to payment gateway...')
            return redirect('orders:payment_gateway', order_id=order.id)
    
    context = {
        'order': order,
        'payment': payment,
    }
    
    return render(request, 'orders/process_payment.html', context)


@login_required
def order_list(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).select_related('vendor')
    
    # Search and filtering
    search_form = OrderSearchForm(request.GET)
    if search_form.is_valid():
        order_number = search_form.cleaned_data.get('order_number')
        status = search_form.cleaned_data.get('status')
        payment_status = search_form.cleaned_data.get('payment_status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if order_number:
            orders = orders.filter(order_number__icontains=order_number)
        if status:
            orders = orders.filter(status=status)
        if payment_status:
            orders = orders.filter(payment_status=payment_status)
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """Detailed view of an order"""
    order = get_object_or_404(
        Order.objects.select_related('vendor', 'billing_address', 'shipping_address'),
        id=order_id,
        user=request.user
    )
    
    order_items = order.items.all()
    payments = order.payments.all()
    status_history = order.status_history.select_related('changed_by').all()
    
    context = {
        'order': order,
        'order_items': order_items,
        'payments': payments,
        'status_history': status_history,
    }
    
    return render(request, 'orders/order_detail.html', context)


@login_required
def vendor_order_list(request):
    """Vendor's order management"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'You must be a vendor to access this page.')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    orders = Order.objects.filter(vendor=vendor_profile).select_related('user')
    
    # Filtering
    filter_form = VendorOrderFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        payment_status = filter_form.cleaned_data.get('payment_status')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if status:
            orders = orders.filter(status=status)
        if payment_status:
            orders = orders.filter(payment_status=payment_status)
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    total_revenue = orders.filter(payment_status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'total_revenue': total_revenue,
        'vendor_profile': vendor_profile,
    }
    
    return render(request, 'orders/vendor/order_list.html', context)


@login_required
def vendor_order_detail(request, order_id):
    """Vendor's detailed view of an order"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'You must be a vendor to access this page.')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    order = get_object_or_404(
        Order.objects.select_related('user', 'billing_address', 'shipping_address'),
        id=order_id,
        vendor=vendor_profile
    )
    
    order_items = order.items.all()
    payments = order.payments.all()
    status_history = order.status_history.select_related('changed_by').all()
    
    # Status update form
    if request.method == 'POST':
        status_form = OrderStatusUpdateForm(request.POST)
        if status_form.is_valid():
            new_status = status_form.cleaned_data['status']
            notes = status_form.cleaned_data['notes']
            
            if new_status != order.status:
                # Update order status
                order.status = new_status
                
                # Set timestamp based on status
                if new_status == 'confirmed':
                    order.confirmed_at = timezone.now()
                elif new_status == 'shipped':
                    order.shipped_at = timezone.now()
                elif new_status == 'delivered':
                    order.delivered_at = timezone.now()
                elif new_status == 'cancelled':
                    order.cancelled_at = timezone.now()
                
                order.save()
                
                # Create status history
                OrderStatusHistory.objects.create(
                    order=order,
                    status=new_status,
                    changed_by=request.user,
                    notes=notes
                )
                
                messages.success(request, f'Order status updated to {new_status}')
                return redirect('orders:vendor_order_detail', order_id=order.id)
    else:
        status_form = OrderStatusUpdateForm(initial={'status': order.status})
    
    context = {
        'order': order,
        'order_items': order_items,
        'payments': payments,
        'status_history': status_history,
        'status_form': status_form,
    }
    
    return render(request, 'orders/vendor/order_detail.html', context)


@login_required
@require_POST
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_cancel:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', order_id=order.id)
    
    with transaction.atomic():
        # Update order status
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()
        
        # Restore product stock
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            changed_by=request.user,
            notes='Order cancelled by customer'
        )
        
        # Process refund if paid
        if order.payment_status == 'paid':
            payment = order.payments.first()
            if payment.payment_method == 'wallet':
                # Refund to wallet
                wallet = request.user.wallet
                wallet.current_balance += order.total_amount
                wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='credit',
                    amount=order.total_amount,
                    order_id=order.order_number,
                    status='completed',
                    description=f'Refund for cancelled order {order.order_number}',
                    balance_before=wallet.current_balance - order.total_amount,
                    balance_after=wallet.current_balance
                )
            
            order.payment_status = 'refunded'
            order.save()
        
        messages.success(request, 'Order cancelled successfully!')
    
    return redirect('orders:order_detail', order_id=order.id)


# Admin views for order management
@login_required
def admin_order_list(request):
    """Admin view for managing all orders"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    orders = Order.objects.select_related('user', 'vendor')
    
    # Search and filtering
    search_form = OrderSearchForm(request.GET)
    if search_form.is_valid():
        order_number = search_form.cleaned_data.get('order_number')
        status = search_form.cleaned_data.get('status')
        payment_status = search_form.cleaned_data.get('payment_status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        if order_number:
            orders = orders.filter(order_number__icontains=order_number)
        if status:
            orders = orders.filter(status=status)
        if payment_status:
            orders = orders.filter(payment_status=payment_status)
        if date_from:
            orders = orders.filter(created_at__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_orders = orders.count()
    total_revenue = orders.filter(payment_status='paid').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    pending_orders = orders.filter(status='pending').count()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
    }
    
    return render(request, 'orders/admin/order_list.html', context)

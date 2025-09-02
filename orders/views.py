from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, OrderItem
from products.models import Cart
from wallet.models import Wallet, WalletTransaction
from core.models import Address


@login_required
def order_list(request):
    """List user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'orders/list.html', {'orders': page_obj})


@login_required
def order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


@login_required
def create_order(request):
    """Create order from cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product__vendor').all()
        
        if not cart_items:
            messages.error(request, 'Your cart is empty!')
            return redirect('products:cart')
        
        # Get user addresses
        user_addresses = request.user.addresses.all()
        
        if request.method == 'GET':
            # Render checkout form
            context = {
                'cart': cart,
                'cart_items': cart_items,
                'user_addresses': user_addresses,
            }
            return render(request, 'orders/create.html', context)
        
        # Handle POST request
        address_id = request.POST.get('address_id')
        notes = request.POST.get('notes', '')
        coupon_code = request.POST.get('coupon_code', '').strip()
        
        if not address_id:
            messages.error(request, 'Please select a delivery address')
            return redirect('orders:create')
        
        try:
            address = request.user.addresses.get(id=address_id)
        except:
            messages.error(request, 'Invalid delivery address')
            return redirect('orders:create')
        
        # Check wallet balance
        wallet = Wallet.objects.get(user=request.user)
        if wallet.current_balance < cart.total_amount:
            messages.error(request, 'Insufficient wallet balance!')
            return redirect('products:cart')

        with transaction.atomic():
            # Create order for each vendor
            vendor_orders = {}
            for item in cart_items:
                vendor = item.product.vendor
                if vendor not in vendor_orders:
                    order = Order.objects.create(
                        user=request.user,
                        vendor=vendor,
                        delivery_address={
                            'name': address.full_name,
                            'phone': address.phone_number,
                            'address': address.street_address,
                            'city': address.city,
                            'state': address.state,
                            'postal_code': address.postal_code,
                            'address_type': address.address_type
                        },
                        subtotal=0,
                        total_amount=0,
                        notes=notes,
                        payment_method='wallet',
                        payment_status='paid',
                        order_status='placed',
                        escrow_status='held'
                    )
                    vendor_orders[vendor] = order
                
                # Create order item
                OrderItem.objects.create(
                    order=vendor_orders[vendor],
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    total_price=item.total_price
                )
                
                # Update order totals
                vendor_orders[vendor].subtotal += item.total_price
                vendor_orders[vendor].total_amount += item.total_price
            
            # Save updated orders and process payments
            for order in vendor_orders.values():
                # Apply coupon if provided
                if coupon_code:
                    try:
                        from coupons.views import apply_coupon_to_order
                        success, message = apply_coupon_to_order(order, coupon_code, request.user)
                        if success:
                            messages.success(request, message)
                    except:
                        pass
                
                order.save()
                
                # Hold amount in wallet
                wallet.current_balance -= order.total_amount
                wallet.held_amount += order.total_amount
                wallet.save()
                
                # Create wallet transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='hold',
                    amount=order.total_amount,
                    order_id=str(order.id),
                    status='completed',
                    description=f'Payment held for order #{order.order_number}',
                    balance_before=wallet.current_balance + order.total_amount,
                    balance_after=wallet.current_balance
                )
            
            # Clear cart
            cart_items.delete()
            
            if len(vendor_orders) == 1:
                order = list(vendor_orders.values())[0]
                messages.success(request, f'Order #{order.order_number} placed successfully!')
                return redirect('orders:detail', order_id=order.id)
            else:
                messages.success(request, f'{len(vendor_orders)} orders placed successfully!')
                return redirect('orders:list')
        
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty!')
        return redirect('products:cart')
    except Exception as e:
        messages.error(request, f'Error creating order: {str(e)}')
        return redirect('products:cart')


@login_required
@require_POST
def update_order_status(request, order_id):
    """Update order status (vendor only)"""
    order = get_object_or_404(Order, id=order_id, vendor__user=request.user)
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.ORDER_STATUS_CHOICES):
        order.order_status = new_status
        order.save()
        messages.success(request, f'Order status updated to {order.get_order_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('orders:detail', order_id=order.id)


@login_required
@require_POST
def cancel_order(request, order_id):
    """Cancel order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.order_status in ['placed', 'confirmed']:
        order.order_status = 'cancelled'
        order.save()
        
        # Release held amount back to wallet
        wallet = request.user.wallet
        wallet.current_balance += order.total_amount
        wallet.held_amount -= order.total_amount
        wallet.save()
        
        # Create refund transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='refund',
            amount=order.total_amount,
            order_id=str(order.id),
            status='completed',
            description=f'Refund for cancelled order #{order.order_number}',
            balance_before=wallet.current_balance - order.total_amount,
            balance_after=wallet.current_balance
        )
        
        messages.success(request, 'Order cancelled successfully')
    else:
        messages.error(request, 'Order cannot be cancelled at this stage')
    
    return redirect('orders:detail', order_id=order.id)

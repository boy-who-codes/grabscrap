from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import Coupon, CouponUsage
import json


@require_POST
def validate_coupon(request):
    """AJAX endpoint to validate coupon code"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        order_amount = float(data.get('order_amount', 0))
        
        if not code:
            return JsonResponse({'valid': False, 'message': 'Please enter a coupon code'})
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return JsonResponse({'valid': False, 'message': 'Invalid coupon code'})
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'valid': False, 'message': 'Please login to use coupons'})
        
        # Validate coupon
        is_valid, message = coupon.can_use(request.user, order_amount)
        
        if is_valid:
            discount = coupon.calculate_discount(order_amount)
            return JsonResponse({
                'valid': True,
                'message': 'Coupon applied successfully!',
                'discount': float(discount),
                'coupon_id': str(coupon.id),
                'code': coupon.code
            })
        else:
            return JsonResponse({'valid': False, 'message': message})
            
    except Exception as e:
        return JsonResponse({'valid': False, 'message': 'Error validating coupon'})


@login_required
def vendor_coupons(request):
    """Vendor coupon management page"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, "Access denied. Vendor account required.")
        return redirect('core:home')
    
    vendor = request.user.vendor_profile
    coupons = Coupon.objects.filter(vendor=vendor).order_by('-created_at')
    
    return render(request, 'coupons/vendor_list.html', {
        'coupons': coupons,
        'vendor': vendor
    })


@login_required
def create_vendor_coupon(request):
    """Create new vendor coupon"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, "Access denied. Vendor account required.")
        return redirect('core:home')
    
    if request.method == 'POST':
        try:
            vendor = request.user.vendor_profile
            
            coupon = Coupon.objects.create(
                code=request.POST['code'].upper(),
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                discount_type=request.POST['discount_type'],
                discount_value=request.POST['discount_value'],
                max_discount=request.POST.get('max_discount') or None,
                min_order_amount=request.POST.get('min_order_amount', 0),
                coupon_type='vendor',
                vendor=vendor,
                created_by=request.user,
                usage_limit=request.POST.get('usage_limit') or None,
                user_limit=request.POST.get('user_limit', 1),
                valid_from=request.POST['valid_from'],
                valid_until=request.POST['valid_until'],
                is_active=True
            )
            
            messages.success(request, f"Coupon '{coupon.code}' created successfully!")
            return redirect('coupons:vendor_list')
            
        except Exception as e:
            messages.error(request, f"Error creating coupon: {str(e)}")
    
    return render(request, 'coupons/vendor_create.html')


def apply_coupon_to_order(order, coupon_code, user):
    """Apply coupon to order - used during checkout"""
    try:
        coupon = Coupon.objects.get(code=coupon_code.upper())
        
        # Validate coupon
        is_valid, message = coupon.can_use(user, order.total_amount)
        if not is_valid:
            return False, message
        
        # Check if coupon is vendor-specific and matches order vendor
        if coupon.coupon_type == 'vendor' and coupon.vendor != order.vendor:
            return False, "This coupon is not valid for this vendor"
        
        # Calculate discount
        discount = coupon.calculate_discount(order.total_amount)
        
        # Apply discount to order
        order.coupon_discount = discount
        order.total_amount -= discount
        order.save()
        
        # Record usage
        CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order=order,
            discount_amount=discount
        )
        
        # Update coupon usage count
        coupon.used_count += 1
        coupon.save()
        
        return True, f"Coupon applied! You saved ₹{discount}"
        
    except Coupon.DoesNotExist:
        return False, "Invalid coupon code"
    except Exception as e:
        return False, f"Error applying coupon: {str(e)}"

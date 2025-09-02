from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from vendors.models import Vendor
from chat.models import ChatMessage, ChatModeration
from coupons.models import Coupon, CouponUsage
from advertisements.models import Advertisement
from orders.models import Order
from core.models import User, Category
from products.models import Product
from wallet.models import Wallet, WalletTransaction


@staff_member_required
def admin_dashboard(request):
    """Enhanced admin dashboard with comprehensive analytics"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic stats
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'total_vendors': Vendor.objects.count(),
        'pending_kyc': Vendor.objects.filter(kyc_status='pending').count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(order_status='placed').count(),
        'flagged_messages': ChatMessage.objects.filter(is_flagged=True).count(),
        'active_coupons': Coupon.objects.filter(is_active=True).count(),
        'active_ads': Advertisement.objects.filter(status='active').count(),
    }
    
    # Revenue analytics
    revenue_data = Order.objects.filter(payment_status='paid').aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('id'),
        avg_order_value=Avg('total_amount')
    )
    
    commission_rate = 0.05  # 5% commission
    total_commission = (revenue_data['total_revenue'] or 0) * commission_rate
    
    # Escrow management
    escrow_stats = Order.objects.aggregate(
        held_amount=Sum('total_amount', filter=Q(escrow_status='held')),
        pending_release=Count('id', filter=Q(escrow_status='held', order_status='delivered')),
        disputed_orders=Count('id', filter=Q(escrow_status='disputed'))
    )
    
    # Wallet analytics
    wallet_stats = WalletTransaction.objects.aggregate(
        total_recharges=Sum('amount', filter=Q(transaction_type='recharge', status='completed')),
        total_transactions=Count('id', filter=Q(status='completed'))
    )
    
    # Recent activities
    recent_orders = Order.objects.select_related('user', 'vendor').order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    pending_escrow = Order.objects.filter(
        escrow_status='held', 
        order_status='delivered'
    ).select_related('user', 'vendor')[:5]
    
    # Chart data for analytics
    daily_orders = Order.objects.filter(
        created_at__gte=week_ago
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('day')
    
    context = {
        'stats': stats,
        'revenue_data': revenue_data,
        'total_commission': total_commission,
        'escrow_stats': escrow_stats,
        'wallet_stats': wallet_stats,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'pending_escrow': pending_escrow,
        'daily_orders': list(daily_orders),
    }
    
    return render(request, 'custom_admin/dashboard.html', context)


@staff_member_required
def user_analytics(request):
    """Detailed user analytics"""
    today = timezone.now().date()
    
    # User growth data
    user_growth = User.objects.extra(
        select={'month': "DATE_FORMAT(date_joined, '%%Y-%%m')"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # User activity stats
    user_stats = {
        'total_users': User.objects.count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'active_users': User.objects.filter(last_login__gte=today - timedelta(days=30)).count(),
        'banned_users': User.objects.filter(is_banned=True).count(),
        'vendor_users': User.objects.filter(is_vendor=True).count(),
    }
    
    # Top users by orders
    top_users = User.objects.annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).filter(order_count__gt=0).order_by('-total_spent')[:10]
    
    context = {
        'user_stats': user_stats,
        'user_growth': list(user_growth),
        'top_users': top_users,
    }
    
    return render(request, 'custom_admin/user_analytics.html', context)


@staff_member_required
def escrow_management(request):
    """Escrow payment management"""
    # Orders pending release
    pending_release = Order.objects.filter(
        escrow_status='held',
        order_status='delivered'
    ).select_related('user', 'vendor').order_by('-updated_at')
    
    # Disputed orders
    disputed_orders = Order.objects.filter(
        escrow_status='disputed'
    ).select_related('user', 'vendor').order_by('-updated_at')
    
    # Escrow statistics
    escrow_stats = Order.objects.aggregate(
        total_held=Sum('total_amount', filter=Q(escrow_status='held')),
        total_released=Sum('total_amount', filter=Q(escrow_status='released')),
        pending_count=Count('id', filter=Q(escrow_status='held')),
        disputed_count=Count('id', filter=Q(escrow_status='disputed'))
    )
    
    context = {
        'pending_release': pending_release,
        'disputed_orders': disputed_orders,
        'escrow_stats': escrow_stats,
    }
    
    return render(request, 'custom_admin/escrow_management.html', context)


@staff_member_required
@require_POST
def release_escrow(request, order_id):
    """Release escrow payment to vendor"""
    order = get_object_or_404(Order, id=order_id)
    
    if order.escrow_status == 'held':
        order.escrow_status = 'released'
        order.save()
        
        # Create commission record here if needed
        messages.success(request, f'Payment released for order #{order.order_number}')
    else:
        messages.error(request, 'Order payment cannot be released')
    
    return redirect('custom_admin:escrow_management')


@staff_member_required
@require_POST
def dispute_escrow(request, order_id):
    """Mark order as disputed"""
    order = get_object_or_404(Order, id=order_id)
    reason = request.POST.get('reason', 'Admin dispute')
    
    order.escrow_status = 'disputed'
    order.notes = f"Disputed: {reason}"
    order.save()
    
    messages.warning(request, f'Order #{order.order_number} marked as disputed')
    return redirect('custom_admin:escrow_management')


@staff_member_required
def kyc_verification(request):
    """Enhanced KYC verification panel"""
    pending_kyc = Vendor.objects.filter(kyc_status='pending').select_related('user')
    approved_kyc = Vendor.objects.filter(kyc_status='approved').select_related('user')[:10]
    rejected_kyc = Vendor.objects.filter(kyc_status='rejected').select_related('user')[:10]
    
    # KYC statistics
    kyc_stats = {
        'pending': Vendor.objects.filter(kyc_status='pending').count(),
        'approved': Vendor.objects.filter(kyc_status='approved').count(),
        'rejected': Vendor.objects.filter(kyc_status='rejected').count(),
        'total': Vendor.objects.count(),
    }
    
    context = {
        'pending_kyc': pending_kyc,
        'approved_kyc': approved_kyc,
        'rejected_kyc': rejected_kyc,
        'kyc_stats': kyc_stats,
    }
    
    return render(request, 'custom_admin/kyc_verification.html', context)


@staff_member_required
@require_POST
def approve_kyc(request, vendor_id):
    """Approve vendor KYC"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.kyc_status = 'approved'
    vendor.kyc_rejection_reason = ''
    vendor.save()
    
    # Update user type
    vendor.user.user_type = 'vendor'
    vendor.user.save()
    
    messages.success(request, f'KYC approved for {vendor.store_name}')
    return redirect('custom_admin:kyc_verification')


@staff_member_required
@require_POST
def reject_kyc(request, vendor_id):
    """Reject vendor KYC"""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    reason = request.POST.get('reason', 'Documents not clear')
    vendor.kyc_status = 'rejected'
    vendor.kyc_rejection_reason = reason
    vendor.save()
    
    messages.warning(request, f'KYC rejected for {vendor.store_name}')
    return redirect('custom_admin:kyc_verification')


@staff_member_required
def chat_moderation(request):
    """Enhanced chat moderation panel"""
    flagged_messages = ChatMessage.objects.filter(
        is_flagged=True
    ).select_related('sender', 'room').order_by('-created_at')
    
    pending_moderations = ChatModeration.objects.filter(
        is_reviewed=False
    ).select_related('message__sender', 'message__room').order_by('-created_at')
    
    # Moderation statistics
    mod_stats = {
        'flagged_count': flagged_messages.count(),
        'pending_count': pending_moderations.count(),
        'total_messages': ChatMessage.objects.count(),
        'violation_rate': (flagged_messages.count() / max(ChatMessage.objects.count(), 1)) * 100
    }
    
    context = {
        'flagged_messages': flagged_messages,
        'pending_moderations': pending_moderations,
        'mod_stats': mod_stats,
    }
    
    return render(request, 'custom_admin/chat_moderation.html', context)


@staff_member_required
@require_POST
def moderate_message(request, message_id):
    """Moderate a flagged message"""
    message = get_object_or_404(ChatMessage, id=message_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        message.is_flagged = False
        message.save()
        messages.success(request, 'Message approved')
    elif action == 'delete':
        message.delete()
        messages.success(request, 'Message deleted')
    elif action == 'warn':
        message.is_flagged = False
        message.save()
        messages.info(request, 'User warned and message approved')
    
    return redirect('custom_admin:chat_moderation')


@staff_member_required
def commission_management(request):
    """Enhanced commission management"""
    commission_data = Order.objects.filter(
        payment_status='paid'
    ).values('vendor__store_name', 'vendor__id').annotate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount'),
        commission_earned=Sum('total_amount') * 0.05
    ).order_by('-total_revenue')[:20]
    
    total_stats = Order.objects.filter(payment_status='paid').aggregate(
        total_revenue=Sum('total_amount'),
        total_commission=Sum('total_amount') * 0.05,
        total_orders=Count('id')
    )
    
    context = {
        'commission_data': commission_data,
        'total_stats': total_stats,
        'commission_rate': 5.0,
    }
    
    return render(request, 'custom_admin/commission_management.html', context)


@staff_member_required
def coupon_management(request):
    """Enhanced coupon management"""
    active_coupons = Coupon.objects.filter(is_active=True).select_related('vendor', 'created_by')
    expired_coupons = Coupon.objects.filter(
        Q(valid_until__lt=timezone.now()) | Q(is_active=False)
    ).select_related('vendor', 'created_by')[:10]
    
    coupon_stats = CouponUsage.objects.values(
        'coupon__code', 'coupon__name'
    ).annotate(
        usage_count=Count('id'),
        total_discount=Sum('discount_amount')
    ).order_by('-usage_count')[:10]
    
    # Overall coupon statistics
    overall_stats = {
        'active_count': active_coupons.count(),
        'total_usage': CouponUsage.objects.count(),
        'total_savings': CouponUsage.objects.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0,
        'avg_discount': CouponUsage.objects.aggregate(Avg('discount_amount'))['discount_amount__avg'] or 0,
    }
    
    context = {
        'active_coupons': active_coupons,
        'expired_coupons': expired_coupons,
        'coupon_stats': coupon_stats,
        'overall_stats': overall_stats,
    }
    
    return render(request, 'custom_admin/coupon_management.html', context)


@staff_member_required
def advertisement_management(request):
    """Enhanced advertisement management"""
    active_ads = Advertisement.objects.filter(status='active')
    expired_ads = Advertisement.objects.filter(status='expired')[:10]
    
    ad_stats = Advertisement.objects.values(
        'title', 'placement'
    ).annotate(
        total_impressions=Sum('impressions'),
        total_clicks=Sum('clicks')
    ).order_by('-total_impressions')[:10]
    
    # Overall ad statistics
    overall_stats = Advertisement.objects.aggregate(
        total_impressions=Sum('impressions'),
        total_clicks=Sum('clicks'),
        active_count=Count('id', filter=Q(status='active')),
        avg_ctr=Avg('clicks') / Avg('impressions') * 100 if Advertisement.objects.aggregate(Avg('impressions'))['impressions__avg'] else 0
    )
    
    context = {
        'active_ads': active_ads,
        'expired_ads': expired_ads,
        'ad_stats': ad_stats,
        'overall_stats': overall_stats,
    }
    
    return render(request, 'custom_admin/advertisement_management.html', context)


@staff_member_required
def user_management(request):
    """Enhanced user management"""
    # Pagination for users
    users_list = User.objects.order_by('-date_joined')
    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    banned_users = User.objects.filter(is_banned=True)
    
    user_stats = {
        'total_users': User.objects.count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'banned_users': User.objects.filter(is_banned=True).count(),
        'vendors': User.objects.filter(is_vendor=True).count(),
        'active_today': User.objects.filter(last_login__date=timezone.now().date()).count(),
    }
    
    context = {
        'users': users,
        'banned_users': banned_users,
        'user_stats': user_stats,
    }
    
    return render(request, 'custom_admin/user_management.html', context)


@staff_member_required
@require_POST
def toggle_user_ban(request, user_id):
    """Toggle user ban status"""
    user = get_object_or_404(User, id=user_id)
    user.is_banned = not user.is_banned
    user.save()
    
    status = 'banned' if user.is_banned else 'unbanned'
    messages.success(request, f'User {user.username} has been {status}')
    
    return redirect('custom_admin:user_management')

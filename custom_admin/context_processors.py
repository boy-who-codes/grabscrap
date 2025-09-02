from django.db.models import Count, Q
from vendors.models import Vendor
from chat.models import ChatMessage
from orders.models import Order


def admin_stats(request):
    """Global admin statistics for sidebar badges"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    try:
        stats = {
            'pending_kyc': Vendor.objects.filter(kyc_status='pending').count(),
            'flagged_messages': ChatMessage.objects.filter(is_flagged=True).count(),
        }
        
        escrow_stats = {
            'pending_release': Order.objects.filter(
                escrow_status='held', 
                order_status='delivered'
            ).count(),
        }
        
        return {
            'stats': stats,
            'escrow_stats': escrow_stats,
        }
    except:
        return {
            'stats': {'pending_kyc': 0, 'flagged_messages': 0},
            'escrow_stats': {'pending_release': 0},
        }

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Advertisement, AdClick, AdImpression
import json


def get_active_ads(placement='banner'):
    """Get active advertisements for a specific placement"""
    now = timezone.now()
    return Advertisement.objects.filter(
        status='active',
        start_date__lte=now,
        end_date__gte=now,
        placement=placement
    )


@csrf_exempt
@require_POST
def track_impression(request):
    """Track ad impression"""
    try:
        data = json.loads(request.body)
        ad_id = data.get('ad_id')
        
        ad = get_object_or_404(Advertisement, id=ad_id)
        
        # Create impression record
        AdImpression.objects.create(
            advertisement=ad,
            user=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )
        
        # Update impression count
        ad.impressions += 1
        ad.save(update_fields=['impressions'])
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def track_click(request, ad_id):
    """Track ad click and redirect"""
    ad = get_object_or_404(Advertisement, id=ad_id)
    
    # Create click record
    AdClick.objects.create(
        advertisement=ad,
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Update click count
    ad.clicks += 1
    ad.save(update_fields=['clicks'])
    
    return redirect(ad.click_url)

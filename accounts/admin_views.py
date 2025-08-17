from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.conf import settings
from accounts.models import User, VendorProfile
from products.models import Location, Product

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get location statistics
    total_locations = Location.objects.filter(is_active=True).count()
    locations_with_vendors = Location.objects.filter(
        is_active=True,
        id__in=VendorProfile.objects.values('locations')
    ).count()
    locations_with_products = Location.objects.filter(
        is_active=True,
        id__in=Product.objects.values('available_locations')
    ).count()
    
    # Get user statistics
    total_users = User.objects.count()
    total_vendors = User.objects.filter(user_type='vendor').count()
    total_buyers = User.objects.filter(user_type='buyer').count()
    
    # Get product statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    
    # Get active locations for map
    active_locations = Location.objects.filter(is_active=True)
    
    context = {
        'total_locations': total_locations,
        'locations_with_vendors': locations_with_vendors,
        'locations_with_products': locations_with_products,
        'total_users': total_users,
        'total_vendors': total_vendors,
        'total_buyers': total_buyers,
        'total_products': total_products,
        'active_products': active_products,
        'locations': active_locations,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)
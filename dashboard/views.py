from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from products.models import Location
from kyc_management.models import KYCApplication

@login_required
def admin_dashboard(request):
    User = get_user_model()
    
    context = {
        'total_users': User.objects.filter(is_vendor=False).count(),
        'total_vendors': User.objects.filter(is_vendor=True).count(),
        'total_locations': Location.objects.count(),
        'pending_kyc': KYCApplication.objects.filter(status='pending').count(),
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)
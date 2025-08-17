from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import Category, CategoryRequest
from accounts.models import VendorProfile

@staff_member_required
def category_management(request):
    categories = Category.objects.all().prefetch_related('subcategories')
    pending_requests = CategoryRequest.objects.filter(status='pending').select_related('vendor', 'category')
    
    return render(request, 'products/category_management.html', {
        'categories': categories,
        'pending_requests': pending_requests
    })

@staff_member_required
def handle_category_request(request, request_id):
    category_request = get_object_or_404(CategoryRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['approve', 'reject']:
            category_request.status = action
            category_request.reviewed_by = request.user
            category_request.reviewed_at = timezone.now()
            
            if action == 'reject':
                category_request.rejection_reason = request.POST.get('rejection_reason', '')
            
            category_request.save()
            messages.success(request, f'Request {action}ed successfully')
            return redirect('category_management')
    
    return render(request, 'products/review_category_request.html', {
        'request': category_request
    })

@staff_member_required
def update_commission_rates(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        commission_rate = request.POST.get('commission_rate') or None
        
        try:
            category = Category.objects.get(id=category_id)
            category.commission_rate = commission_rate
            category.save()
            messages.success(request, f'Commission rate updated for {category.name}')
        except (Category.DoesNotExist, ValueError) as e:
            messages.error(request, 'Invalid category selection')
    
    categories = Category.objects.filter(parent_category=None).prefetch_related('subcategories')
    return render(request, 'products/commission_rates.html', {'categories': categories})
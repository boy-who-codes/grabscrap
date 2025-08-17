from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Location, Product
from .forms import LocationForm


@login_required
def location_list(request):
    """Admin view for managing locations"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    locations = Location.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        locations = locations.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )
    
    # Add statistics
    locations = locations.annotate(
        product_count=Count('products', distinct=True),
        vendor_count=Count('products__vendor', distinct=True)
    )
    
    # Pagination
    paginator = Paginator(locations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_locations': locations.count(),
    }
    
    return render(request, 'products/admin/location_list.html', context)


@login_required
def location_create(request):
    """Admin view for creating locations"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" created successfully!')
            return redirect('products:location_list')
    else:
        form = LocationForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'products/admin/location_form.html', context)


@login_required
def location_edit(request, location_id):
    """Admin view for editing locations"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    location = get_object_or_404(Location, id=location_id)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            location = form.save()
            messages.success(request, f'Location "{location.name}" updated successfully!')
            return redirect('products:location_list')
    else:
        form = LocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
        'action': 'Edit',
    }
    
    return render(request, 'products/admin/location_form.html', context)


@login_required
@require_POST
def location_toggle_status(request, location_id):
    """Toggle location active/inactive status"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    location = get_object_or_404(Location, id=location_id)
    location.is_active = not location.is_active
    location.save()
    
    status = 'activated' if location.is_active else 'deactivated'
    return JsonResponse({
        'success': True,
        'message': f'Location {status} successfully!',
        'is_active': location.is_active
    })


@login_required
def location_map(request):
    """Display all locations on a map"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    locations = Location.objects.filter(is_active=True).annotate(
        product_count=Count('products', distinct=True),
        vendor_count=Count('products__vendor', distinct=True)
    )
    
    context = {
        'locations': locations,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'products/admin/location_map.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from accounts.models import User, VendorProfile
from .models import Category, Product, ProductImage, ProductReview, Wishlist
from .forms import CategoryForm, ProductForm, ProductImageForm, ProductReviewForm, ProductSearchForm


def product_list(request):
    """Display all active products with search and filtering"""
    products = Product.objects.filter(is_active=True, vendor__kyc_status='approved')
    
    # Search and filtering
    search_form = ProductSearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        category = search_form.cleaned_data.get('category')
        min_price = search_form.cleaned_data.get('min_price')
        max_price = search_form.cleaned_data.get('max_price')
        unit = search_form.cleaned_data.get('unit')
        in_stock_only = search_form.cleaned_data.get('in_stock_only')
        featured_only = search_form.cleaned_data.get('featured_only')
        
        if query:
            # Create a query for text fields
            text_query = Q(title__icontains=query) | \
                        Q(description__icontains=query) | \
                        Q(vendor__store_name__icontains=query)
            
            # Check if we're using SQLite
            from django.db import connection
            if 'sqlite' in connection.vendor:
                # For SQLite, we'll filter in Python for tags
                # First filter by text fields
                products = products.filter(text_query)
                
                # Then filter by tags in Python
                if query.strip():
                    filtered_pks = []
                    for product in products:
                        if any(query.lower() in tag.lower() for tag in (product.tags or [])):
                            filtered_pks.append(product.pk)
                    products = products.filter(pk__in=filtered_pks)
            else:
                # For other databases, use the original query
                products = products.filter(
                    text_query |
                    Q(tags__contains=[query])
                )
        
        if category:
            products = products.filter(category=category)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)
        
        if unit:
            products = products.filter(unit=unit)
        
        if in_stock_only:
            products = products.filter(stock_quantity__gt=0)
        
        if featured_only:
            products = products.filter(is_featured=True)
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for sidebar
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'categories': categories,
        'total_products': products.count(),
    }
    
    return render(request, 'products/product_list.html', context)


def product_detail(request, product_id):
    """Display detailed product information"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Increment view count
    product.increment_views()
    
    # Get related products from same vendor
    related_products = Product.objects.filter(
        vendor=product.vendor,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Get product reviews
    reviews = ProductReview.objects.filter(product=product, is_approved=True)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user has this product in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Review form
    review_form = None
    if request.user.is_authenticated:
        # Check if user has purchased this product
        has_purchased = False  # TODO: Implement order checking
        if has_purchased:
            review_form = ProductReviewForm()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'in_wishlist': in_wishlist,
        'review_form': review_form,
    }
    
    return render(request, 'products/product_detail.html', context)


@login_required
def vendor_product_list(request):
    """Vendor's product management dashboard"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'You must be a vendor to access this page.')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    products = Product.objects.filter(vendor=vendor_profile)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'out_of_stock':
        products = products.filter(stock_quantity=0)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    out_of_stock = products.filter(stock_quantity=0).count()
    total_views = products.aggregate(Sum('views_count'))['views_count__sum'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock': out_of_stock,
        'total_views': total_views,
        'vendor_profile': vendor_profile,
    }
    
    return render(request, 'products/vendor/product_list.html', context)


@login_required
def vendor_product_create(request):
    """Create new product for vendor"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'You must be a vendor to access this page.')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, vendor=vendor_profile)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor_profile
            product.save()
            
            # Handle single image upload
            image = request.FILES.get('images')
            if image:
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=True,
                    sort_order=0
                )
            
            messages.success(request, f'Product "{product.title}" created successfully!')
            return redirect('products:vendor_product_list')
    else:
        form = ProductForm(vendor=vendor_profile)
    
    context = {
        'form': form,
        'vendor_profile': vendor_profile,
    }
    
    return render(request, 'products/vendor/product_form.html', context)


@login_required
def vendor_product_edit(request, product_id):
    """Edit existing product"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'You must be a vendor to access this page.')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    product = get_object_or_404(Product, id=product_id, vendor=vendor_profile)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, vendor=vendor_profile)
        if form.is_valid():
            product = form.save()
            
            # Handle new image
            image = request.FILES.get('images')
            if image:
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    sort_order=product.images.count()
                )
            
            messages.success(request, f'Product "{product.title}" updated successfully!')
            return redirect('products:vendor_product_list')
    else:
        form = ProductForm(instance=product, vendor=vendor_profile)
    
    context = {
        'form': form,
        'product': product,
        'vendor_profile': vendor_profile,
    }
    
    return render(request, 'products/vendor/product_form.html', context)


@login_required
@require_POST
def vendor_product_toggle_status(request, product_id):
    """Toggle product active/inactive status"""
    if not hasattr(request.user, 'vendor_profile'):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    vendor_profile = request.user.vendor_profile
    product = get_object_or_404(Product, id=product_id, vendor=vendor_profile)
    
    product.is_active = not product.is_active
    product.save()
    
    status = 'activated' if product.is_active else 'deactivated'
    return JsonResponse({
        'success': True,
        'message': f'Product {status} successfully!',
        'is_active': product.is_active
    })


@login_required
@require_POST
def vendor_product_delete(request, product_id):
    """Delete product (soft delete)"""
    if not hasattr(request.user, 'vendor_profile'):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    vendor_profile = request.user.vendor_profile
    product = get_object_or_404(Product, id=product_id, vendor=vendor_profile)
    
    product.is_active = False
    product.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Product "{product.title}" deleted successfully!'
    })


@login_required
def add_to_wishlist(request, product_id):
    """Add product to user's wishlist"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f'"{product.title}" added to wishlist!')
    else:
        messages.info(request, f'"{product.title}" is already in your wishlist!')
    
    return redirect('products:product_detail', product_id=product_id)


@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from user's wishlist"""
    product = get_object_or_404(Product, id=product_id)
    
    try:
        wishlist_item = Wishlist.objects.get(user=request.user, product=product)
        wishlist_item.delete()
        messages.success(request, f'"{product.title}" removed from wishlist!')
    except Wishlist.DoesNotExist:
        messages.error(request, 'Product not found in wishlist!')
    
    return redirect('products:wishlist')


@login_required
def wishlist(request):
    """Display user's wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    context = {
        'wishlist_items': wishlist_items,
    }
    
    return render(request, 'products/wishlist.html', context)


@login_required
@require_POST
def add_review(request, product_id):
    """Add product review"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Check if user has already reviewed this product
    if ProductReview.objects.filter(user=request.user, product=product).exists():
        messages.error(request, 'You have already reviewed this product!')
        return redirect('products:product_detail', product_id=product_id)
    
    form = ProductReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        
        messages.success(request, 'Review submitted successfully!')
    else:
        messages.error(request, 'Please correct the errors in your review.')
    
    return redirect('products:product_detail', product_id=product_id)


def category_list(request):
    """Display all categories"""
    categories = Category.objects.filter(is_active=True, parent_category=None)
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'products/category_list.html', context)


def category_detail(request, category_id):
    """Display products in a specific category"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    products = Product.objects.filter(
        category=category,
        is_active=True,
        vendor__kyc_status='approved'
    )
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'total_products': products.count(),
    }
    
    return render(request, 'products/category_detail.html', context)


# Admin views for category management
@login_required
def admin_category_list(request):
    """Admin view for managing categories"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    categories = Category.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'products/admin/category_list.html', context)


@login_required
def admin_category_create(request):
    """Admin view for creating categories"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('products:admin_category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'products/admin/category_form.html', context)


@login_required
def admin_category_edit(request, category_id):
    """Admin view for editing categories"""
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('products:admin_category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'Edit',
    }
    
    return render(request, 'products/admin/category_form.html', context)

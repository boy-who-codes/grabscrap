from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Product, ProductImage, Wishlist, Cart, CartItem
from .serializers import ProductSerializer, ProductImageSerializer, WishlistSerializer
from core.models import Category


def products_list(request):
    """Products listing with filters"""
    products = Product.objects.filter(is_active=True).select_related('vendor', 'category')
    categories = Category.objects.filter(is_active=True)
    
    # Filters
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', 'created_at')
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search_query:
        products = products.filter(title__icontains=search_query)
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'popular':
        products = products.order_by('-orders_count')
    else:
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'products/list.html', context)


def product_detail(request, product_id):
    """Product detail view"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Increment view count
    product.views_count += 1
    product.save(update_fields=['views_count'])
    
    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product_id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'products/detail.html', context)


@login_required
def product_create(request):
    """Create new product (vendor only)"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Only vendors can create products!')
        return redirect('vendors:register_form')
    
    vendor = request.user.vendor_profile
    if vendor.kyc_status != 'approved':
        messages.error(request, 'Please complete KYC verification before adding products!')
        return redirect('vendors:kyc_form')
    
    if request.method == 'POST':
        # Handle product creation
        messages.success(request, 'Product creation feature coming soon!')
        return redirect('vendors:products')
    
    return render(request, 'products/create.html')


@login_required
def cart_view(request):
    """Shopping cart page"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product', 'product__vendor').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'products/cart.html', context)


@login_required
@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.title} added to cart',
            'cart_count': cart.total_items
        })
    
    messages.success(request, f'{product.title} added to cart!')
    return redirect('products:detail', product_id=product_id)


@login_required
@require_http_methods(["POST"])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = cart_item.cart if quantity > 0 else Cart.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'cart_total': float(cart.total_amount),
            'cart_count': cart.total_items
        })
    
    return redirect('products:cart')


@login_required
@require_http_methods(["POST"])
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_title = cart_item.product.title
    cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product_title} removed from cart'
        })
    
    messages.success(request, f'{product_title} removed from cart!')
    return redirect('products:cart')


# API Views
class ProductListView(generics.ListAPIView):
    """Product list API"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset.order_by('-created_at')


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail API"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_active=True)


class VendorProductListView(generics.ListCreateAPIView):
    """Vendor products management"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(vendor__user=self.request.user)
    
    def perform_create(self, serializer):
        vendor = self.request.user.vendor_profile
        serializer.save(vendor=vendor)


class VendorProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vendor product detail management"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(vendor__user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_wishlist(request, product_id):
    """Toggle product in wishlist"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist', 'in_wishlist': False})
        else:
            return Response({'message': 'Added to wishlist', 'in_wishlist': True})
            
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_add_to_cart(request, product_id):
    """API endpoint to add product to cart"""
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        quantity = int(request.data.get('quantity', 1))
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'success': True,
            'message': f'{product.title} added to cart',
            'cart_count': cart.total_items
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

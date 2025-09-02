from django.contrib import admin
from .models import Product, ProductImage, Wishlist, ProductReview, Cart, CartItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'vendor__store_name', 'sku')
    readonly_fields = ('sku', 'views_count', 'orders_count', 'created_at', 'updated_at')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'alt_text')
    list_filter = ('is_primary',)
    search_fields = ('product__title', 'alt_text')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_amount', 'created_at')
    readonly_fields = ('total_items', 'total_amount', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price', 'created_at')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__title')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__title')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('user__username', 'product__title')

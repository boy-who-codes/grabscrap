from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, Product, ProductImage, ProductReview, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'is_active', 'sort_order', 'total_products', 'commission_rate']
    list_filter = ['is_active', 'parent_category']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order', 'commission_rate']
    prepopulated_fields = {'name': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'parent_category')
        }),
        ('Display Settings', {
            'fields': ('icon', 'is_active', 'sort_order')
        }),
        ('Commission', {
            'fields': ('commission_rate',),
            'description': 'Commission rate in percentage (overrides global rate)'
        }),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'vendor', 'category', 'price', 'unit', 'stock_quantity', 
        'is_active', 'is_featured', 'views_count', 'orders_count', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_featured', 'category', 'unit', 'vendor__kyc_status',
        'created_at', 'updated_at'
    ]
    search_fields = ['title', 'description', 'sku', 'vendor__store_name']
    list_editable = ['is_active', 'is_featured', 'stock_quantity']
    readonly_fields = ['sku', 'views_count', 'orders_count', 'created_at', 'updated_at']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'category', 'title', 'description', 'sku')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'unit', 'stock_quantity', 'minimum_order_quantity')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'tags', 'specifications')
        }),
        ('Statistics', {
            'fields': ('views_count', 'orders_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor', 'category')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__title', 'alt_text']
    list_editable = ['is_primary', 'sort_order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'title', 'is_verified_purchase', 
        'is_approved', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__title', 'user__full_name', 'title', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'user', 'rating', 'title', 'comment')
        }),
        ('Status', {
            'fields': ('is_verified_purchase', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__full_name', 'user__email', 'product__title']
    readonly_fields = ['added_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')

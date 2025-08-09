from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Public product views
    path('', views.product_list, name='product_list'),
    path('product/<uuid:product_id>/', views.product_detail, name='product_detail'),
    path('category/', views.category_list, name='category_list'),
    path('category/<uuid:category_id>/', views.category_detail, name='category_detail'),
    
    # User wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<uuid:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Product reviews
    path('product/<uuid:product_id>/review/', views.add_review, name='add_review'),
    
    # Vendor product management
    path('vendor/', views.vendor_product_list, name='vendor_product_list'),
    path('vendor/create/', views.vendor_product_create, name='vendor_product_create'),
    path('vendor/edit/<uuid:product_id>/', views.vendor_product_edit, name='vendor_product_edit'),
    path('vendor/toggle/<uuid:product_id>/', views.vendor_product_toggle_status, name='vendor_product_toggle_status'),
    path('vendor/delete/<uuid:product_id>/', views.vendor_product_delete, name='vendor_product_delete'),
    
    # Admin category management
    path('admin/categories/', views.admin_category_list, name='admin_category_list'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/edit/<uuid:category_id>/', views.admin_category_edit, name='admin_category_edit'),
] 
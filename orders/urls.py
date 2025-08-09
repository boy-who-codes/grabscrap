from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [

    
    # Cart management
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<uuid:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Checkout and payment
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<uuid:order_id>/', views.process_payment, name='process_payment'),
    
    # User order management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Vendor order management
    path('vendor/orders/', views.vendor_order_list, name='vendor_order_list'),
    path('vendor/orders/<uuid:order_id>/', views.vendor_order_detail, name='vendor_order_detail'),
    
    # Admin order management
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
] 
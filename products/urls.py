from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Template views
    path('', views.products_list, name='list'),
    path('create/', views.product_create, name='create'),
    path('<uuid:product_id>/', views.product_detail, name='detail'),
    
    # Cart views
    path('cart/', views.cart_view, name='cart'),
    path('<uuid:product_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<uuid:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]

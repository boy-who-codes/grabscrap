from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Template views
    path('', views.order_list, name='list'),
    path('create/', views.create_order, name='create'),
    path('<uuid:order_id>/', views.order_detail, name='detail'),
    path('<uuid:order_id>/update-status/', views.update_order_status, name='update_status'),
    path('<uuid:order_id>/cancel/', views.cancel_order, name='cancel'),
]

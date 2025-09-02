from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat views
    path('', views.chat_list, name='list'),
    path('dashboard/', views.chat_dashboard, name='dashboard'),
    path('room/<uuid:room_id>/', views.chat_room, name='room'),
    path('room/<uuid:room_id>/send/', views.send_message, name='send_message'),
    
    # API endpoints
    path('api/products/<int:product_id>/chat/', views.create_product_chat, name='create_product_chat'),
    
    # Admin moderation
    path('moderation/', views.admin_moderation, name='moderation'),
]

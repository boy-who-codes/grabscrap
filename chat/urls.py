from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('room/<int:order_id>/', views.chat_room, name='chat_room'),
    path('list/', views.chat_list, name='chat_list'),
    path('unread-count/', views.get_unread_count, name='get_unread_count'),
]
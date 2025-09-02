from django.urls import path
from . import views
from .notification_views import NotificationListView

app_name = 'core'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<uuid:notification_id>/delete/', views.delete_notification, name='delete_notification'),
]

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """Full notifications page"""
    model = Notification
    template_name = 'core/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return context


# Utility function to create notifications
def create_notification(user, title, message, notification_type='system', data=None):
    """Helper function to create notifications"""
    return Notification.create_notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data
    )

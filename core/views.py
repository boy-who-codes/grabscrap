from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Notification


def home(request):
    """Home page view"""
    return render(request, 'core/home.html')


def health_check(request):
    """Health check endpoint"""
    return render(request, 'core/health.html', {'status': 'ok'})


@login_required
def get_notifications(request):
    """Get user notifications page"""
    notifications = Notification.objects.filter(user=request.user)[:15]
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count
    }
    return render(request, 'core/notifications.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        messages.success(request, 'Notification marked as read.')
    except Exception as e:
        messages.error(request, 'Failed to mark notification as read.')
    
    return redirect('core:notifications')


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
    except Exception as e:
        messages.error(request, 'Failed to mark all notifications as read.')
    
    return redirect('core:notifications')


@login_required
@require_http_methods(["POST"])
def delete_notification(request, notification_id):
    """Delete notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.delete()
        messages.success(request, 'Notification deleted.')
    except Exception as e:
        messages.error(request, 'Failed to delete notification.')
    
    return redirect('core:notifications')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Notification
import json


def home(request):
    """Home page view"""
    return render(request, 'core/home.html')


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'ok'})


@login_required
def get_notifications(request):
    """Get user notifications for the bell icon"""
    notifications = Notification.objects.filter(user=request.user)[:15]
    unread_count = notifications.filter(is_read=False).count()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'data': notification.data
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Notification marked as read.')
            return redirect('core:notifications')
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, 'Failed to mark notification as read.')
            return redirect('core:notifications')


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'All notifications marked as read.')
            return redirect('core:notifications')
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, 'Failed to mark all notifications as read.')
            return redirect('core:notifications')


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Notification deleted.')
            return redirect('core:notifications')
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            messages.error(request, 'Failed to delete notification.')
            return redirect('core:notifications')

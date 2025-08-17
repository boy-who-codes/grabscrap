from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import ChatRoom, Message
from orders.models import Order


@login_required
def chat_room(request, order_id):
    """View for displaying chat room for a specific order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user is authorized to access this chat (buyer or vendor)
    if request.user != order.user and request.user != order.vendor.user:
        return redirect('orders:order_list')
    
    # Get or create chat room for this order
    chat_room, created = ChatRoom.objects.get_or_create(order=order)
    
    # Mark all messages as read for the current user
    Message.objects.filter(
        chat_room=chat_room
    ).exclude(
        sender=request.user
    ).update(is_read=True)
    
    # Get all messages for this chat room
    messages = Message.objects.filter(chat_room=chat_room)
    
    context = {
        'chat_room': chat_room,
        'messages': messages,
        'order': order,
    }
    
    return render(request, 'chat/chat_room.html', context)


@login_required
def chat_list(request):
    """View for displaying list of active chats for the current user"""
    user = request.user
    
    # Get all orders where the user is either buyer or vendor
    if user.user_type == 'vendor':
        vendor_profile = user.vendor_profile
        orders = Order.objects.filter(vendor=vendor_profile)
    else:  # buyer
        orders = Order.objects.filter(user=user)
    
    # Get chat rooms for these orders
    chat_rooms = ChatRoom.objects.filter(order__in=orders, is_active=True)
    
    # Count unread messages for each chat room
    for chat_room in chat_rooms:
        chat_room.unread_count = Message.objects.filter(
            chat_room=chat_room,
            is_read=False
        ).exclude(sender=user).count()
    
    context = {
        'chat_rooms': chat_rooms,
    }
    
    return render(request, 'chat/chat_list.html', context)


@login_required
def get_unread_count(request):
    """API endpoint to get count of unread messages for the current user"""
    user = request.user
    
    # Get all orders where the user is either buyer or vendor
    if user.user_type == 'vendor':
        vendor_profile = user.vendor_profile
        orders = Order.objects.filter(vendor=vendor_profile)
    else:  # buyer
        orders = Order.objects.filter(user=user)
    
    # Get chat rooms for these orders
    chat_rooms = ChatRoom.objects.filter(order__in=orders, is_active=True)
    
    # Count all unread messages
    unread_count = Message.objects.filter(
        chat_room__in=chat_rooms,
        is_read=False
    ).exclude(sender=user).count()
    
    return JsonResponse({'unread_count': unread_count})
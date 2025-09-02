from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import ChatRoom, ChatMessage, ChatModeration
from .utils import compress_image
from products.models import Product
import uuid
import os


@login_required
@require_POST
def create_product_chat(request, product_id):
    """Create or get chat room for product inquiry"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check if chat room already exists between user and vendor for this product
        existing_room = ChatRoom.objects.filter(
            product=product,
            participants=request.user
        ).filter(participants=product.vendor.user).first()
        
        if existing_room:
            return JsonResponse({'room_id': str(existing_room.id)})
        
        # Create new chat room
        room = ChatRoom.objects.create(
            product=product,
            room_type='product_inquiry'
        )
        room.participants.add(request.user, product.vendor.user)
        
        # Send initial message
        ChatMessage.objects.create(
            room=room,
            sender=request.user,
            message=f"Hi! I'm interested in your product: {product.title}"
        )
        
        return JsonResponse({'room_id': str(room.id)})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def chat_dashboard(request):
    """Chat dashboard showing all user's chat rooms"""
    user_rooms = ChatRoom.objects.filter(participants=request.user, is_active=True).order_by('-last_activity')
    
    context = {
        'rooms': user_rooms,
        'is_admin': request.user.is_admin_user,
    }
    return render(request, 'chat/dashboard.html', context)


@login_required
def chat_list(request):
    """List all chat rooms for user"""
    user_rooms = ChatRoom.objects.filter(participants=request.user, is_active=True).order_by('-last_activity')
    
    context = {
        'rooms': user_rooms,
    }
    return render(request, 'chat/list.html', context)


@login_required
def chat_room(request, room_id):
    """Chat room view"""
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check permissions
    if not request.user.is_admin_user and request.user not in room.participants.all():
        return render(request, 'chat/access_denied.html')
    
    # Get messages
    messages_list = room.messages.all()
    
    # Mark messages as read
    unread_messages = messages_list.exclude(sender=request.user).filter(is_read=False)
    for message in unread_messages:
        message.is_read = True
        message.save()
    
    context = {
        'room': room,
        'messages': messages_list,
        'is_admin': request.user.is_admin_user,
    }
    return render(request, 'chat/room.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request, room_id):
    """Send message to chat room with media support"""
    try:
        room = get_object_or_404(ChatRoom, id=room_id)
        
        # Check permissions
        if request.user not in room.participants.all():
            messages.error(request, 'Not authorized to send messages in this room.')
            return redirect('chat:room', room_id=room_id)
        
        content = request.POST.get('content', '').strip()
        message_type = 'text'
        attachments = []
        
        # Handle file upload
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            
            # Check file size (max 5MB)
            if uploaded_file.size > 5 * 1024 * 1024:
                messages.error(request, 'Image too large (max 5MB)')
                return redirect('chat:room', room_id=room_id)
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if uploaded_file.content_type not in allowed_types:
                messages.error(request, 'Invalid image type')
                return redirect('chat:room', room_id=room_id)
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"chat_images/{uuid.uuid4().hex}{file_extension}"
            
            # Save file
            file_path = default_storage.save(filename, uploaded_file)
            attachments.append({
                'type': 'image',
                'url': f'/media/{file_path}',
                'name': uploaded_file.name,
                'size': uploaded_file.size
            })
            message_type = 'image'
            if not content:
                content = f"📷 {uploaded_file.name}"
        
        if not content and not attachments:
            messages.error(request, 'Message content or image required')
            return redirect('chat:room', room_id=room_id)
        
        # Create message
        message = ChatMessage.objects.create(
            room=room,
            sender=request.user,
            content=content,
            message_type=message_type,
            attachments=attachments
        )
        
        # Check for violations
        from .moderation import ChatModerator
        ChatModerator.check_message(message)
        
        # Update room activity
        room.save()  # This updates last_activity
        
        # For AJAX requests, redirect back to room
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.success(request, 'Message sent successfully!')
        
        return redirect('chat:room', room_id=room_id)
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.error(request, f'Failed to send message: {str(e)}')
        else:
            messages.error(request, f'Failed to send message: {str(e)}')
        return redirect('chat:room', room_id=room_id)


@login_required
def admin_moderation(request):
    """Admin moderation dashboard"""
    if not request.user.is_admin_user:
        return render(request, 'chat/access_denied.html')
    
    # Get flagged content
    flagged_messages = ChatMessage.objects.filter(is_flagged=True).order_by('-created_at')
    pending_moderations = ChatModeration.objects.filter(is_reviewed=False).order_by('-created_at')
    
    context = {
        'flagged_messages': flagged_messages[:20],
        'pending_moderations': pending_moderations[:20],
    }
    return render(request, 'chat/moderation.html', context)

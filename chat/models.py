from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from orders.models import Order

User = get_user_model()


class ChatRoom(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='chat_room', null=True, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='chat_rooms', null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    room_type = models.CharField(max_length=20, choices=[('order', 'Order'), ('product', 'Product'), ('support', 'Support')], default='product')
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    is_active = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.order:
            return f"Chat - {self.order.order_number}"
        elif self.product:
            return f"Chat - {self.product.title}"
        return f"Chat Room {self.id}"


class ChatMessage(BaseModel):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    attachments = models.JSONField(default=list)
    is_read = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=100, blank=True)
    edited_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class ChatMessageRead(BaseModel):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} read {self.message.id}"


class ChatModeration(BaseModel):
    VIOLATION_TYPES = [
        ('contact_sharing', 'Contact Information Sharing'),
        ('external_payment', 'External Payment Request'),
        ('escrow_bypass', 'Escrow Bypass Attempt'),
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam'),
    ]
    
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='moderations')
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPES)
    detected_content = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    admin_action = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Moderation - {self.violation_type} in {self.message.room}"

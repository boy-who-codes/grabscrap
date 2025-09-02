from django.contrib import admin
from .models import ChatRoom, ChatMessage, ChatMessageRead


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('order', 'is_active', 'last_activity', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('order__order_number',)
    filter_horizontal = ('participants',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'message_type', 'content', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('room__order__order_number', 'sender__username', 'content')


@admin.register(ChatMessageRead)
class ChatMessageReadAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('message__content', 'user__username')

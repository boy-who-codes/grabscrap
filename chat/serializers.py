from rest_framework import serializers
from .models import ChatRoom, ChatMessage, ChatMessageRead


class ChatRoomSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    participant_names = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'order', 'order_number', 'participant_names', 'is_active', 'last_activity']
        read_only_fields = ['id', 'participants']
    
    def get_participant_names(self, obj):
        return [user.full_name or user.username for user in obj.participants.all()]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['id', 'room', 'sender', 'edited_at']


class ChatMessageReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessageRead
        fields = '__all__'
        read_only_fields = ['id', 'user', 'read_at']

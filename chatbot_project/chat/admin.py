from django.contrib import admin
from .models import ChatSession, Message, DeliveryTracking

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['session_id']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'content_preview', 'is_user', 'timestamp']
    list_filter = ['is_user', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'status', 'recipient_name', 'current_location', 'rating']
    list_filter = ['status', 'rating']
    search_fields = ['tracking_number', 'recipient_name']
from django.db import models
from django.contrib.auth.models import User

class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Session {self.session_id}"

class Message(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        sender = "User" if self.is_user else "Bot"
        return f"{sender}: {self.content[:50]}"

class DeliveryTracking(models.Model):
    STATUS_CHOICES = [
        ('picked_up', 'Paket Diambil'),
        ('in_transit', 'Dalam Perjalanan'),
        ('in_warehouse', 'Di Gudang'),
        ('out_for_delivery', 'Sedang Dikirim'),
        ('delivered', 'Terkirim'),
        ('damaged', 'Rusak'),
        ('delayed', 'Tertunda'),
        ('lost', 'Hilang'),
    ]
    
    tracking_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    current_location = models.CharField(max_length=200)
    delivery_date = models.DateTimeField(null=True, blank=True)
    recipient_name = models.CharField(max_length=100)
    recipient_phone = models.CharField(max_length=20)
    issues = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.tracking_number} - {self.get_status_display()}"
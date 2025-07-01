import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_project.settings')
django.setup()

from chat.models import DeliveryTracking

def create_sample_data():
    sample_data = [
        {
            'tracking_number': 'FDE123456789',
            'status': 'delivered',
            'current_location': 'Jakarta Pusat',
            'recipient_name': 'Budi Santoso',
            'recipient_phone': '081234567890',
            'issues': '',
            'rating': 5
        },
        {
            'tracking_number': 'FDE987654321',
            'status': 'in_transit',
            'current_location': 'Surabaya',
            'recipient_name': 'Siti Aminah',
            'recipient_phone': '081987654321',
            'issues': '',
            'rating': None
        },
        {
            'tracking_number': 'FDE456789123',
            'status': 'damaged',
            'current_location': 'Bandung',
            'recipient_name': 'Andi Wijaya',
            'recipient_phone': '081456789123',
            'issues': 'Paket basah karena hujan',
            'rating': 2
        },
    ]
    
    for data in sample_data:
        delivery, created = DeliveryTracking.objects.get_or_create(
            tracking_number=data['tracking_number'],
            defaults=data
        )
        if created:
            print(f"✅ Created: {data['tracking_number']}")

if __name__ == '__main__':
    create_sample_data()
    print("🎉 Sample data berhasil dibuat!")
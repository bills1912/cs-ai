import openai
from django.conf import settings
import json
import re
import logging
from .models import DeliveryTracking

logger = logging.getLogger(__name__)

class DeliveryAIService:
    def __init__(self):
        # Initialize OpenAI client dengan API key dari settings
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False
            logger.warning("OpenAI API key not configured")
        
    def get_delivery_data(self, tracking_number):
        """Simulasi data pengiriman berdasarkan tracking number"""
        try:
            delivery = DeliveryTracking.objects.get(tracking_number=tracking_number)
            return {
                'tracking_number': delivery.tracking_number,
                'status': delivery.status,
                'current_location': delivery.current_location,
                'recipient_name': delivery.recipient_name,
                'recipient_phone': delivery.recipient_phone,
                'issues': delivery.issues,
                'rating': delivery.rating,
                'delivery_date': delivery.delivery_date
            }
        except DeliveryTracking.DoesNotExist:
            # Simulasi data jika tidak ada di database
            import random
            status_options = [
                'picked_up', 'in_transit', 'in_warehouse', 
                'out_for_delivery', 'delivered', 'delayed'
            ]
            locations = ['Jakarta', 'Surabaya', 'Medan', 'Bandung', 'Yogyakarta', 'Denpasar']
            
            return {
                'tracking_number': tracking_number,
                'status': random.choice(status_options),
                'current_location': random.choice(locations),
                'recipient_name': 'Customer',
                'recipient_phone': '081234567890',
                'issues': '',
                'rating': None,
                'delivery_date': None
            }
    
    def extract_tracking_number(self, message):
        """Extract tracking number dari pesan user"""
        # Pattern untuk nomor resi (8-15 karakter alphanumeric)
        patterns = [
            r'\b[A-Z]{2,3}[0-9]{8,12}\b',  # FDE123456789
            r'\b[0-9]{10,15}\b',           # 1234567890123
            r'\b[A-Z0-9]{8,15}\b'          # Mixed alphanumeric
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message.upper())
            if matches:
                return matches[0]
        return None
    
    def generate_response(self, user_message, context=None):
        """Generate AI response menggunakan OpenAI ChatGPT"""
        
        # Extract tracking number dari pesan
        tracking_number = self.extract_tracking_number(user_message)
        delivery_data = None
        
        if tracking_number:
            delivery_data = self.get_delivery_data(tracking_number)
        
        # System prompt untuk ChatGPT
        system_prompt = """
        Anda adalah asisten customer service AI untuk perusahaan pengiriman "FastDelivery Express". 
        Anda bertugas membantu pelanggan dengan masalah pengiriman mereka dengan ramah dan profesional.
        
        ATURAN PENTING:
        1. Selalu gunakan bahasa Indonesia yang sopan dan ramah
        2. Berikan solusi konkret untuk setiap masalah
        3. Jika paket dalam kondisi baik/terkirim, minta rating pelayanan 1-5 bintang
        4. Tawarkan bantuan lebih lanjut jika diperlukan
        5. Gunakan emoji yang sesuai untuk membuat percakapan lebih ramah
        6. Maksimal 3 paragraf per response
        7. Jika tidak ada nomor resi, minta pelanggan memberikan nomor resi
        
        JENIS MASALAH yang bisa ditangani:
        - Cek status pengiriman paket
        - Paket belum sampai tujuan  
        - Paket tertahan di gudang
        - Paket rusak/kondisi buruk
        - Keterlambatan pengiriman
        - Rating dan feedback pelayanan
        - Informasi umum tentang layanan
        
        CONTOH NOMOR RESI: FDE123456789, JNE987654321, JNT456789123
        """
        
        # User prompt dengan konteks delivery data
        user_prompt = f"Pesan pelanggan: {user_message}"
        
        if delivery_data:
            status_map = {
                'picked_up': 'Paket sudah diambil dari pengirim',
                'in_transit': 'Paket sedang dalam perjalanan',
                'in_warehouse': 'Paket berada di gudang sortir',
                'out_for_delivery': 'Paket sedang dikirim ke alamat tujuan',
                'delivered': 'Paket sudah berhasil terkirim',
                'damaged': 'Paket mengalami kerusakan',
                'delayed': 'Pengiriman mengalami keterlambatan',
                'lost': 'Paket hilang'
            }
            
            status_description = status_map.get(delivery_data['status'], 'Status tidak diketahui')
            
            user_prompt += f"""
            
            DATA PENGIRIMAN:
            - Nomor Resi: {delivery_data['tracking_number']}
            - Status: {status_description}
            - Lokasi Saat Ini: {delivery_data['current_location']}
            - Penerima: {delivery_data['recipient_name']}
            - Issues: {delivery_data['issues'] or 'Tidak ada masalah'}
            - Rating: {delivery_data['rating'] or 'Belum ada rating'}
            """
        
        # Coba gunakan OpenAI API
        if self.api_available:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                    timeout=10  # 10 detik timeout
                )
                
                ai_response = response.choices[0].message.content.strip()
                logger.info(f"OpenAI API response successful for message: {user_message[:50]}")
                return ai_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return self.get_fallback_response(user_message, delivery_data)
        else:
            return self.get_fallback_response(user_message, delivery_data)
    
    def get_fallback_response(self, user_message, delivery_data=None):
        """Fallback response jika OpenAI tidak tersedia"""
        
        message_lower = user_message.lower()
        
        # Cek tracking number
        if any(word in message_lower for word in ['resi', 'tracking', 'nomor', 'cek', 'lacak']):
            if delivery_data:
                status_map = {
                    'picked_up': 'Paket sudah diambil dari pengirim',
                    'in_transit': 'Paket sedang dalam perjalanan',
                    'in_warehouse': 'Paket berada di gudang sortir',
                    'out_for_delivery': 'Paket sedang dikirim ke alamat tujuan',
                    'delivered': 'Paket sudah berhasil terkirim',
                    'damaged': 'Paket mengalami kerusakan',
                    'delayed': 'Pengiriman mengalami keterlambatan'
                }
                
                status_text = status_map.get(delivery_data['status'], 'Status tidak diketahui')
                
                if delivery_data['status'] == 'delivered':
                    return f"""✅ **Paket Terkirim!**

📦 Nomor Resi: **{delivery_data['tracking_number']}**
📍 Lokasi: {delivery_data['current_location']}
👤 Penerima: {delivery_data['recipient_name']}

Paket Anda sudah berhasil terkirim! 🎉

Bagaimana pengalaman Anda dengan layanan FastDelivery Express? Berikan rating 1-5 bintang untuk membantu kami meningkatkan kualitas pelayanan! ⭐"""

                elif delivery_data['status'] == 'damaged':
                    return f"""😔 **Paket Mengalami Kerusakan**

📦 Nomor Resi: {delivery_data['tracking_number']}
📍 Lokasi: {delivery_data['current_location']}
⚠️ Masalah: {delivery_data['issues'] or 'Paket rusak'}

**Langkah yang dapat Anda lakukan:**
1. 📸 Foto kondisi paket dan barang
2. 📞 Hubungi call center: **1500-888**
3. 💰 Kami akan proses klaim ganti rugi

Tim kami akan segera menindaklanjuti laporan Anda. Mohon maaf atas ketidaknyamanan ini. 🙏"""

                elif delivery_data['status'] == 'delayed':
                    return f"""⏰ **Pengiriman Tertunda**

📦 Nomor Resi: {delivery_data['tracking_number']}
📍 Lokasi Saat Ini: {delivery_data['current_location']}

Maaf atas keterlambatan pengiriman paket Anda. 

**Kami sedang:**
- 🔄 Mengecek status terkini di lapangan
- 📞 Berkoordinasi dengan kurir lokal  
- ⚡ Memprioritaskan pengiriman Anda

Estimasi pengiriman akan kami update via SMS/WhatsApp. Terima kasih atas kesabaran Anda! 🙏"""

                else:
                    return f"""📦 **Status Paket Anda**

📦 Nomor Resi: **{delivery_data['tracking_number']}**
📊 Status: {status_text}
📍 Lokasi Saat Ini: {delivery_data['current_location']}
👤 Penerima: {delivery_data['recipient_name']}

Paket Anda dalam proses pengiriman yang normal. Kami akan update status terbaru segera! 🚚

Ada yang bisa saya bantu lebih lanjut? 😊"""
            else:
                return """📦 **Pelacakan Paket**

Untuk melacak paket Anda, silakan berikan nomor resi.

**Contoh format nomor resi:**
- FDE123456789 (FastDelivery Express)
- JNE987654321 (JNE)
- JNT456789123 (J&T)

Ketik: **"Cek resi [NOMOR_RESI]"**

Atau langsung ketik nomor resi Anda! 📱"""
        
        # Masalah paket rusak
        elif any(word in message_lower for word in ['rusak', 'pecah', 'hancur', 'cacat', 'beda']):
            return """😔 **Laporan Paket Rusak**

Kami sangat menyesal mendengar paket Anda mengalami kerusakan.

**Langkah penanganan:**
1. 📸 **Foto paket** (luar dan dalam)
2. 📞 **Hubungi call center:** 1500-888
3. 📋 **Isi form klaim** melalui customer service
4. 💰 **Proses ganti rugi** max 3 hari kerja

**Butuh nomor resi untuk proses lebih cepat!**

Tim kami akan memastikan Anda mendapat kompensasi yang sesuai. 🤝"""
        
        # Masalah keterlambatan
        elif any(word in message_lower for word in ['terlambat', 'lama', 'belum sampai', 'delay', 'lambat']):
            return """⏰ **Penanganan Keterlambatan**

Kami memahami kekhawatiran Anda tentang keterlambatan pengiriman.

**Yang akan kami lakukan:**
1. 🔍 **Investigasi rute** pengiriman
2. 📞 **Kontak kurir** di lapangan  
3. ⚡ **Prioritas tinggi** untuk paket Anda
4. 📱 **Update real-time** via SMS/WA

**Berikan nomor resi untuk pengecekan detail!**

Kami berkomitmen menyelesaikan masalah ini dengan cepat. 🚀"""
        
        # Rating dan feedback
        elif any(word in message_lower for word in ['rating', 'bintang', 'nilai', 'review', 'puas', 'bagus', 'buruk']):
            return """⭐ **Rating & Feedback**

Terima kasih atas feedback Anda!

**Berikan rating pelayanan:**
- 5⭐ = Sangat Puas
- 4⭐ = Puas  
- 3⭐ = Cukup
- 2⭐ = Kurang Puas
- 1⭐ = Sangat Tidak Puas

Rating Anda sangat membantu kami meningkatkan kualitas layanan FastDelivery Express.

**Ketik: "Rating [1-5] bintang [komentar]"**

Ada saran atau masukan lain? 💭"""
        
        # Sapaan
        elif any(word in message_lower for word in ['halo', 'hai', 'hello', 'selamat', 'pagi', 'siang', 'sore', 'malam']):
            return """👋 **Selamat datang di FastDelivery Express!**

Saya adalah asisten AI customer service yang siap membantu Anda 24/7.

**Layanan yang tersedia:**
- 📦 Cek status pengiriman
- ⏰ Laporan keterlambatan  
- 😔 Laporan paket rusak
- ⭐ Rating & feedback
- 📞 Informasi call center

**Ketik nomor resi atau pilih layanan di atas!**

Ada yang bisa saya bantu hari ini? 😊"""
        
        # Default response
        else:
            return f"""🤖 **FastDelivery Express Customer Service**

Terima kasih atas pesan Anda: *"{user_message}"*

**Layanan yang bisa saya bantu:**
- 📦 **Cek status:** "Cek resi FDE123456789"
- ⏰ **Keterlambatan:** "Paket terlambat" 
- 😔 **Paket rusak:** "Paket saya rusak"
- ⭐ **Rating:** "Rating 5 bintang"

**Call Center 24/7:** 1500-888

Silakan ketik layanan yang Anda butuhkan! 🚀"""
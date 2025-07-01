from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import json
import uuid
import logging
from .ai_service import DeliveryAIService
from .models import ChatSession, Message

logger = logging.getLogger(__name__)

@never_cache
def index(request):
    """Main chat page"""
    return render(request, 'chat/index.html')

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Handle chat messages dengan integrasi OpenAI"""
    try:
        # Parse request data
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        # Validasi input
        if not user_message:
            return JsonResponse({
                'error': 'Pesan tidak boleh kosong',
                'status': 'error'
            }, status=400)
        
        if len(user_message) > 1000:
            return JsonResponse({
                'error': 'Pesan terlalu panjang (maksimal 1000 karakter)',
                'status': 'error'
            }, status=400)
        
        # Create or get chat session
        if not session_id:
            session_id = str(uuid.uuid4())
            
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={'is_active': True}
        )
        
        # Log user message
        logger.info(f"New message from session {session_id}: {user_message[:100]}")
        
        # Save user message to database
        user_msg = Message.objects.create(
            session=session,
            content=user_message,
            is_user=True
        )
        
        # Generate AI response menggunakan OpenAI
        ai_service = DeliveryAIService()
        bot_response = ai_service.generate_response(user_message)
        
        # Save bot response to database
        bot_msg = Message.objects.create(
            session=session,
            content=bot_response,
            is_user=False
        )
        
        # Log successful response
        logger.info(f"AI response generated for session {session_id}: {bot_response[:100]}")
        
        return JsonResponse({
            'response': bot_response,
            'session_id': session_id,
            'status': 'success',
            'message_id': str(bot_msg.id),
            'timestamp': bot_msg.timestamp.isoformat()
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'error': 'Format JSON tidak valid',
            'status': 'error'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return JsonResponse({
            'error': 'Terjadi kesalahan server. Silakan coba lagi.',
            'status': 'error',
            'fallback_response': 'Maaf, sistem sedang mengalami gangguan. Tim teknis kami sedang memperbaikinya. Silakan hubungi call center 1500-888 untuk bantuan langsung. 📞'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submit_rating(request):
    """Handle rating submission"""
    try:
        data = json.loads(request.body)
        rating = data.get('rating')
        comment = data.get('comment', '')
        tracking_number = data.get('tracking_number')
        session_id = data.get('session_id')
        
        # Validasi rating
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return JsonResponse({
                'error': 'Rating harus berupa angka 1-5',
                'status': 'error'
            }, status=400)
        
        # Update delivery tracking jika ada tracking number
        if tracking_number:
            try:
                from .models import DeliveryTracking
                delivery = DeliveryTracking.objects.get(tracking_number=tracking_number)
                delivery.rating = rating
                delivery.save()
                logger.info(f"Rating {rating} saved for tracking {tracking_number}")
            except DeliveryTracking.DoesNotExist:
                logger.warning(f"Tracking number {tracking_number} not found for rating")
        
        # Generate response berdasarkan rating
        if rating >= 4:
            response = f"""⭐ **Terima kasih atas rating {rating} bintang!**

Kami sangat senang Anda puas dengan layanan FastDelivery Express! 🎉

{f"Komentar Anda: '{comment}'" if comment else ""}

Rating Anda membantu kami terus memberikan pelayanan terbaik.

Ada yang bisa saya bantu lagi? 😊"""
        else:
            response = f"""⭐ **Terima kasih atas rating {rating} bintang.**

Kami menyesal layanan kami belum memenuhi harapan Anda. 😔

{f"Komentar Anda: '{comment}'" if comment else ""}

**Tim kami akan:**
- 📋 Review feedback Anda
- 🔄 Perbaiki kualitas layanan  
- 📞 Mungkin menghubungi untuk klarifikasi

Hubungi 1500-888 jika butuh bantuan lebih lanjut. 🤝"""
        
        # Save rating message to chat
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
                Message.objects.create(
                    session=session,
                    content=response,
                    is_user=False
                )
            except ChatSession.DoesNotExist:
                pass
        
        return JsonResponse({
            'response': response,
            'status': 'success',
            'rating_saved': True
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Format JSON tidak valid',
            'status': 'error'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error in submit_rating: {str(e)}")
        return JsonResponse({
            'error': 'Gagal menyimpan rating',
            'status': 'error'
        }, status=500)

@require_http_methods(["GET"])
def chat_history(request, session_id):
    """Get chat history for a session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        
        history = []
        for msg in messages:
            history.append({
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return JsonResponse({
            'history': history,
            'status': 'success'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({
            'error': 'Session tidak ditemukan',
            'status': 'error'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error in chat_history: {str(e)}")
        return JsonResponse({
            'error': 'Gagal mengambil riwayat chat',
            'status': 'error'
        }, status=500)
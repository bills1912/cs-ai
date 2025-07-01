from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='chat_index'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/submit-rating/', views.submit_rating, name='submit_rating'),
    path('api/history/<str:session_id>/', views.chat_history, name='chat_history'),
]
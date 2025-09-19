

from django.urls import path

from .views import ChatbotAPIView

urlpatterns = [
    path('response/', ChatbotAPIView.as_view(), name='chatbot-api'),
]
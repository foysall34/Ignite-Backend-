from django.urls import path
from .views import ChatHistoryView, CreatePremiumSubscriptionView,CreateTopUpCheckoutView,FileUploadView ,UploadStatusView ,FileUploadViewed , QueryView, UserAllChatsView ,VoiceResponseView, TextToVoiceView, stripe_webhook

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload-file'),
    path("upload-file/", FileUploadViewed.as_view(), name="upload"),
    path("upload-status/<int:record_id>/", UploadStatusView.as_view(), name="upload-status"),
    path("query/", QueryView.as_view(), name="query"), 
    path("chat/history/", ChatHistoryView.as_view(), name="chat-history"),
    path("chat/all/", UserAllChatsView.as_view(), name="user-all-chats"),


    path('voice-response/', VoiceResponseView.as_view(), name='voice-response'),
    path("text-to-voice/", TextToVoiceView.as_view(), name="text_to_voice"),
    path("create-subscription/", CreatePremiumSubscriptionView.as_view(), name="create-subscription"),
    path("create-topup/", CreateTopUpCheckoutView.as_view(), name="create-topup"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),


]

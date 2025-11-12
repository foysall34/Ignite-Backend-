from django.urls import path
from .views import CreatePremiumSubscriptionView,CreateTopUpCheckoutView, FileUploadView ,UploadStatusView ,FileUploadViewed , QueryView ,VoiceResponseView, TextToVoiceView, stripe_webhook

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload-file'),
    path("upload-file/", FileUploadViewed.as_view(), name="upload"),
    path("upload-status/<int:record_id>/", UploadStatusView.as_view(), name="upload-status"),
    path("query/", QueryView.as_view(), name="query"), 
    path('voice-response/', VoiceResponseView.as_view(), name='voice-response'),
    path("text-to-voice/", TextToVoiceView.as_view(), name="text_to_voice"),
    path("create-subscription/", CreatePremiumSubscriptionView.as_view(), name="create-subscription"),
    path("create-topup/", CreateTopUpCheckoutView.as_view(), name="create-topup"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),


]

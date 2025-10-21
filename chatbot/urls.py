from django.urls import path
from . import views
from .views import get_presigned_download

urlpatterns = [
    path('presign/', views.get_presigned_post, name='get_presigned_post'),
    path('confirm-upload/', views.confirm_upload, name='confirm_upload'),
    path('download/', get_presigned_download , name='pre-sig')
]

from django.urls import path
from .views import FileUploadView ,UploadStatusView ,FileUploadViewed , QueryView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='upload-file'),
    path("upload-file/", FileUploadViewed.as_view(), name="upload"),
    path("upload-status/<int:record_id>/", UploadStatusView.as_view(), name="upload-status"),
    path("query/", QueryView.as_view(), name="query"), 
]

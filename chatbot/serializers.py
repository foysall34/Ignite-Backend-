from rest_framework import serializers
from .models import UploadedFile

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'uploader', 'file', 's3_key', 'filename', 'content_type', 'size', 'created_at']
        read_only_fields = ['id', 'uploader', 'created_at']

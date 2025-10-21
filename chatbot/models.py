from django.db import models
from django.conf import settings

class UploadedFile(models.Model):
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)
    s3_key = models.CharField(max_length=1024, blank=True) 
    filename = models.CharField(max_length=512, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename or (self.file.name if self.file else self.s3_key)


from django.db import models

class UploadFile(models.Model):
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name



from django.db import models

class UploadRecord(models.Model):
    ROLE_CHOICES = (("admin","admin"), ("user","user"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    original_name = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="pending") 
    error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.original_name} - {self.status}"

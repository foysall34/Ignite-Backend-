
from django.db import models
from django.conf import settings
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
    category = models.CharField(max_length=100, null=True, blank=True)


    def __str__(self):
        return f"{self.original_name} - {self.status}"




class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)





class QueryHistory(models.Model):
    

    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages" , null=True, blank=True )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , null=True, blank=True )
    query = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.created_at}"
    



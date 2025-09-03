from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Profile(models.Model):
    ROLE_CHOICES = (
        ('free_user', 'Free User'),
        ('premium_user', 'Premium User'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='free_user')
    otp = models.CharField(max_length=4, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile - {self.get_role_display()}"

    def is_otp_expired(self):
        if self.otp_created_at:
            return timezone.now() > self.otp_created_at + datetime.timedelta(minutes=5)
        return True
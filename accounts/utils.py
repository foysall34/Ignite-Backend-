import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """Generate a 4-digit OTP."""
    return str(random.randint(1000, 9999))

def send_otp_email(email, otp):
    """Send OTP to the user's email."""
    subject = 'Your OTP for Registration'
    message = f'Your OTP is: {otp}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

def send_password_reset_otp_email(email, otp):
    """Send Password Reset OTP to the user's email."""
    subject = 'Your Password Reset OTP'
    message = f'Your OTP to reset your password is: {otp}'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
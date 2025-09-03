# users/utils.py

import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():

    return str(random.randint(1000, 9999))

def send_otp_via_email(email, otp):
    subject = 'Your Account Verification OTP'
    message = f'Your OTP for account verification is: {otp}. It is valid for 5 minutes.'
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email])
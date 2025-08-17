import random
import time
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string

def generate_otp(length=settings.OTP_LENGTH):
    """Generate a random OTP of specified length"""
    numbers = '0123456789'
    return ''.join(random.choice(numbers) for _ in range(length))

def send_otp_email(email, otp):
    """Send OTP to user's email"""
    subject = 'Your OTP for Login'
    message = f'Your OTP is: {otp}'
    html_message = render_to_string('emails/otp_email.html', {'otp': otp})
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )

def verify_otp(email, otp):
    """Verify if the provided OTP is valid"""
    cache_key = f'otp_{email}'
    cached_otp = cache.get(cache_key)
    
    if cached_otp and cached_otp == otp:
        cache.delete(cache_key)  # Delete the OTP after successful verification
        return True
    return False

def store_otp(email, otp):
    """Store OTP in cache with expiration"""
    cache_key = f'otp_{email}'
    cache.set(cache_key, otp, timeout=settings.OTP_EXPIRY_SECONDS)
    return otp

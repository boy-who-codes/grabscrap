import random
import string
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from user_agents import parse


def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def get_current_site_url(request=None):
    """Get current site URL based on request or settings"""
    if request:
        protocol = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        return f"{protocol}://{host}"
    
    # Fallback to settings
    return getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info(request):
    """Extract device information from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    parsed = parse(user_agent)
    
    return {
        'browser': f"{parsed.browser.family} {parsed.browser.version_string}",
        'os': f"{parsed.os.family} {parsed.os.version_string}",
        'device': parsed.device.family,
        'is_mobile': parsed.is_mobile,
        'is_tablet': parsed.is_tablet,
        'is_pc': parsed.is_pc,
    }


def get_location_info(ip_address):
    """Get location information from IP address"""
    try:
        # Using ipapi.co for location (free tier)
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
            }
    except:
        pass
    
    return {
        'city': 'Unknown',
        'region': 'Unknown', 
        'country': 'Unknown',
        'timezone': 'Unknown',
    }


def send_otp_email(user, otp_code, purpose='login', request=None):
    """Send OTP via email with proper configuration"""
    subject_map = {
        'login': 'Login Verification Code',
        'password_reset': 'Password Reset Code',
        'email_verify': 'Email Verification Code'
    }
    
    subject = f"KABAADWALA™ - {subject_map.get(purpose, 'Verification Code')}"
    
    # Get site URL for email template
    site_url = get_current_site_url(request)
    
    html_message = render_to_string('emails/otp_email.html', {
        'user': user,
        'otp_code': otp_code,
        'purpose': purpose,
        'expires_in': 10,  # minutes
        'site_url': site_url,
    })
    
    # Use environment email settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'KABAADWALA <noreply@kabaadwala.com>')
    
    send_mail(
        subject=subject,
        message=f'Your verification code is: {otp_code}',
        from_email=from_email,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )


def send_login_alert(user, login_history, request=None):
    """Send login alert email"""
    subject = "KABAADWALA™ - New Login Alert"
    
    # Get site URL for email template
    site_url = get_current_site_url(request)
    
    html_message = render_to_string('emails/login_alert.html', {
        'user': user,
        'login_history': login_history,
        'login_time': login_history.created_at,
        'site_url': site_url,
    })
    
    # Use environment email settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'KABAADWALA <noreply@kabaadwala.com>')
    
    send_mail(
        subject=subject,
        message=f'New login detected from IP: {login_history.ip_address}',
        from_email=from_email,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True
    )


def send_activation_email(user, request=None):
    """Send account activation email with proper host URL"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    
    # Generate activation token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Get site URL
    site_url = get_current_site_url(request)
    activation_url = f"{site_url}/accounts/verify/{uid}/{token}/"
    
    subject = "KABAADWALA™ - Activate Your Account"
    
    html_message = render_to_string('emails/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
        'site_url': site_url,
    })
    
    # Use environment email settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'KABAADWALA <noreply@kabaadwala.com>')
    
    send_mail(
        subject=subject,
        message=f'Please activate your account by clicking: {activation_url}',
        from_email=from_email,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False
    )

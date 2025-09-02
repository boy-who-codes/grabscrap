from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import sys

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task
def send_verification_email(user_id, request_host=None):
    """Send email verification to user with proper host detection"""
    try:
        user = User.objects.get(id=user_id)
        
        # Use the send_activation_email function from utils
        from core.utils import send_activation_email
        
        # Create a mock request object with host info if provided
        class MockRequest:
            def __init__(self, host):
                self.host = host
            
            def get_host(self):
                return self.host or 'localhost:8000'
            
            def is_secure(self):
                return self.host and self.host.startswith('https')
        
        mock_request = MockRequest(request_host) if request_host else None
        
        # Send activation email
        send_activation_email(user, mock_request)
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {str(e)}")
        return False


@shared_task
def send_otp_email_task(user_id, otp_code, purpose='login'):
    """Send OTP for 2FA authentication"""
    try:
        user = User.objects.get(id=user_id)
        
        # Use the send_otp_email function from utils
        from core.utils import send_otp_email
        send_otp_email(user, otp_code, purpose)
        
        logger.info(f'OTP email sent to {user.email}')
        return f'OTP sent to {user.email}'
    except Exception as e:
        logger.error(f'Failed to send OTP: {str(e)}')
        return f'Failed to send OTP: {str(e)}'


@shared_task
def send_mobile_otp(mobile_number):
    """Send OTP to mobile number via SMS"""
    import random
    from django.core.cache import cache
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in cache for 5 minutes
    cache.set(f'mobile_otp_{mobile_number}', otp, timeout=300)
    
    # Console output for development - using print for immediate visibility
    print(f"\n" + "="*50)
    print(f"📱 SMS OTP for {mobile_number}: {otp}")
    print(f"⏰ Valid for 5 minutes")
    print("="*50 + "\n")
    
    # Also flush stdout to ensure immediate display
    sys.stdout.flush()
    
    # Also log it
    logger.info(f"SMS OTP for {mobile_number}: {otp}")
    
    try:
        # TODO: Replace with actual SMS service integration
        message = f"Your KABAADWALA™ verification OTP is: {otp}. Valid for 5 minutes. Do not share with anyone."
        
        # In production, uncomment and configure your SMS provider:
        # return send_sms_via_provider(mobile_number, message)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send SMS OTP to {mobile_number}: {str(e)}")
        logger.error(f"Failed to send SMS OTP to {mobile_number}: {str(e)}")
        return False


@shared_task
def send_notification(user_id, notification_type, message, data=None):
    """Send real-time notification to user"""
    try:
        group_name = f'notifications_{user_id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_message',
                'notification_type': notification_type,
                'message': message,
                'data': data or {}
            }
        )
        logger.info(f'Notification sent to user {user_id}')
        return f'Notification sent to user {user_id}'
    except Exception as e:
        logger.error(f'Failed to send notification: {str(e)}')
        return f'Failed to send notification: {str(e)}'


@shared_task
def cleanup_expired_sessions():
    """Clean up expired user sessions"""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired_sessions.count()
    expired_sessions.delete()
    
    logger.info(f'Cleaned up {count} expired sessions')
    return f'Cleaned up {count} expired sessions'


@shared_task
def generate_daily_report():
    """Generate daily platform statistics"""
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get user statistics
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__date=yesterday).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    report = {
        'date': str(yesterday),
        'total_users': total_users,
        'new_users': new_users,
        'verified_users': verified_users,
    }
    
    logger.info(f'Daily report generated: {report}')
    return report

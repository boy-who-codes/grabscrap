import re
from django.core.mail import send_mail
from django.conf import settings
from .models import ChatModeration


class ChatModerator:
    """Chat moderation system to detect policy violations"""
    
    # Patterns for detecting violations
    CONTACT_PATTERNS = [
        r'\b\d{10}\b',  # Phone numbers
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone with separators
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\bwhatsapp\b', r'\btelegram\b', r'\binstagram\b',  # Social media
    ]
    
    EXTERNAL_PAYMENT_PATTERNS = [
        r'\bpaytm\b', r'\bgpay\b', r'\bphonepe\b', r'\bupi\b',
        r'\bcash\b', r'\bdirect\b.*\bpay\b', r'\boutside\b.*\bapp\b',
        r'\bbank\b.*\btransfer\b', r'\bneft\b', r'\brtgs\b',
    ]
    
    ESCROW_BYPASS_PATTERNS = [
        r'\bbypass\b', r'\bavoid\b.*\bfee\b', r'\bdirect\b.*\bdeal\b',
        r'\bno\b.*\bcommission\b', r'\boff\b.*\bplatform\b',
        r'\bmeet\b.*\bperson\b', r'\bcash\b.*\bdelivery\b',
    ]
    
    @classmethod
    def check_message(cls, message):
        """Check message for policy violations"""
        content = message.content.lower()
        violations = []
        
        # Check for contact sharing
        for pattern in cls.CONTACT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(('contact_sharing', 'Contact information detected'))
                break
        
        # Check for external payment
        for pattern in cls.EXTERNAL_PAYMENT_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(('external_payment', 'External payment method detected'))
                break
        
        # Check for escrow bypass
        for pattern in cls.ESCROW_BYPASS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(('escrow_bypass', 'Escrow bypass attempt detected'))
                break
        
        # Create moderation records and flag message
        if violations:
            message.is_flagged = True
            message.flagged_reason = violations[0][1]
            message.save()
            
            for violation_type, detected_content in violations:
                ChatModeration.objects.create(
                    message=message,
                    violation_type=violation_type,
                    detected_content=detected_content
                )
            
            # Notify admin
            cls.notify_admin(message, violations)
        
        return violations
    
    @classmethod
    def notify_admin(cls, message, violations):
        """Send notification to admin about policy violation"""
        try:
            violation_types = [v[0] for v in violations]
            
            subject = f"Chat Policy Violation Detected - {', '.join(violation_types)}"
            message_content = f"""
Policy violation detected in chat:

Room: {message.room}
Sender: {message.sender.full_name} ({message.sender.email})
Message: {message.content}
Violations: {', '.join([v[1] for v in violations])}
Time: {message.created_at}

Please review and take appropriate action.
"""
            
            send_mail(
                subject,
                message_content,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send admin notification: {e}")

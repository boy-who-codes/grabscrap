from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

@shared_task
def send_email_task(subject, to_email, template_name, context):
    try:
        html_content = render_to_string(template_name, context)
        msg = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as exc:
        logging.error(f"Celery email task failed: {exc}")
        return False 
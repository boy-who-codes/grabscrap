#!/usr/bin/env python
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kabaadwala.settings')
django.setup()

from core.tasks import send_verification_email
from core.models import User
import uuid

print("=" * 60)
print("📧 KABAADWALA™ - Email Console Test")
print("=" * 60)

# Create test user
email = f'console{uuid.uuid4().hex[:6]}@test.com'
try:
    user = User.objects.create_user(
        username=email,
        email=email,
        full_name='Console Test User',
        password='testpass123'
    )
    
    print(f"👤 Created user: {user.email}")
    print("📧 Sending verification email...")
    print("-" * 60)
    
    # Send email - this will show in console
    result = send_verification_email(str(user.id))
    
    print("-" * 60)
    print(f"✅ Email sent successfully: {result}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 60)

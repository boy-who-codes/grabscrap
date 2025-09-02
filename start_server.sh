#!/bin/bash
echo "🚀 Starting KABAADWALA™ Development Server"
echo "=========================================="
echo "📧 Emails will appear in this console"
echo "🌐 Server: http://127.0.0.1:8000"
echo "📝 Signup: http://127.0.0.1:8000/accounts/register/"
echo "🔐 Login: http://127.0.0.1:8000/accounts/login/"
echo "=========================================="
echo ""

cd "/mnt/d/0000Paid Projects/Kwala_backend"
source kabaadwala_env/bin/activate
python manage.py runserver 127.0.0.1:8000

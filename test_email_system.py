#!/usr/bin/env python3
"""Comprehensive email system test"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("EMAIL SYSTEM TEST")
print("=" * 60)

# Test 1: Import email service
print("\n1. Testing email service import...")
try:
    from backend.email_service import email_service, EmailConfig
    print("   ✅ Email service imported successfully")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check configuration
print("\n2. Testing email configuration...")
is_configured = EmailConfig.is_configured()
print(f"   Email enabled: {EmailConfig.EMAIL_ENABLED}")
print(f"   SMTP host: {EmailConfig.SMTP_HOST}")
print(f"   SMTP port: {EmailConfig.SMTP_PORT}")
print(f"   From email: {EmailConfig.SMTP_FROM_EMAIL}")
print(f"   Configured: {is_configured}")

if not is_configured:
    print("   ⚠️  Email not configured - set EMAIL_ENABLED=true and SMTP credentials")
else:
    print("   ✅ Email is configured")

# Test 3: Template rendering
print("\n3. Testing template rendering...")
templates_to_test = [
    'welcome.html',
    'document_processed.html',
    'password_reset.html',
    'api_key_created.html',
    'quota_warning.html',
    'admin_alert.html'
]

all_templates_ok = True
for template_name in templates_to_test:
    try:
        html = email_service.render_template(
            template_name,
            username='TestUser',
            login_url='http://localhost:8501',
            filename='test.pdf',
            chunks_count=10,
            reset_url='http://localhost:8501/reset?token=test',
            expiry_hours=24,
            key_name='Test Key',
            usage_percent=85.5,
            limit=100,
            subject='Test Alert',
            message='This is a test message',
            severity='info',
            timestamp='2025-01-22T12:00:00'
        )
        if html:
            print(f"   ✅ {template_name} - {len(html)} chars")
        else:
            print(f"   ⚠️  {template_name} - empty output")
            all_templates_ok = False
    except Exception as e:
        print(f"   ❌ {template_name} - Error: {e}")
        all_templates_ok = False

if all_templates_ok:
    print("   ✅ All templates render successfully")
else:
    print("   ⚠️  Some templates have issues")

# Test 4: Email tasks
print("\n4. Testing Celery email tasks...")
try:
    from backend.tasks import EMAIL_TASKS_AVAILABLE
    print(f"   Email tasks available: {EMAIL_TASKS_AVAILABLE}")
    
    if EMAIL_TASKS_AVAILABLE:
        from backend.tasks import (
            send_welcome_email_task,
            send_document_processed_email_task,
            send_quota_warning_email_task
        )
        print("   ✅ All email tasks imported")
        print(f"   - send_welcome_email_task: {send_welcome_email_task}")
        print(f"   - send_document_processed_email_task: {send_document_processed_email_task}")
        print(f"   - send_quota_warning_email_task: {send_quota_warning_email_task}")
    else:
        print("   ⚠️  Email tasks not available (email_service not imported)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Integration check
print("\n5. Testing integration with main.py...")
try:
    # Check if email is integrated in registration
    with open('backend/main.py', 'r') as f:
        content = f.read()
        if 'send_welcome_email_task' in content:
            print("   ✅ Welcome email integrated in registration")
        else:
            print("   ⚠️  Welcome email not found in main.py")
except Exception as e:
    print(f"   ❌ Error checking integration: {e}")

# Test 6: Frontend page
print("\n6. Testing frontend email settings page...")
if os.path.exists('frontend/pages/10_📧_Email_Settings.py'):
    print("   ✅ Email settings page exists")
else:
    print("   ❌ Email settings page not found")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

if is_configured:
    print("✅ Email system is configured and ready")
    print("💡 Run 'python email_test.py' to send a test email")
else:
    print("⚠️  Email system is not configured")
    print("💡 Configure SMTP settings in .env to enable email")

print("=" * 60)


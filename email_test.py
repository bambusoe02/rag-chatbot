#!/usr/bin/env python3
"""Test email configuration"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.email_service import email_service, EmailConfig

async def test_email():
    """Test email sending"""
    
    print("📧 Email Configuration Test\n")
    print("=" * 50)
    
    # Check configuration
    if not EmailConfig.is_configured():
        print("❌ Email not configured!")
        print("\nPlease set these environment variables:")
        print("  - EMAIL_ENABLED=true")
        print("  - SMTP_USERNAME=your-email@gmail.com")
        print("  - SMTP_PASSWORD=your-app-password")
        return
    
    print("✅ Email configuration found")
    print(f"SMTP Host: {EmailConfig.SMTP_HOST}")
    print(f"SMTP Port: {EmailConfig.SMTP_PORT}")
    print(f"From: {EmailConfig.SMTP_FROM_EMAIL}")
    print()
    
    # Ask for test email
    test_email = input("Enter email to send test to: ").strip()
    
    if not test_email:
        print("❌ No email provided")
        return
    
    print(f"\n📤 Sending test email to {test_email}...")
    
    # Send test email
    success = await email_service.send_email(
        to_email=test_email,
        subject="RAG Chatbot - Test Email",
        html_body="""
        <h1>Test Email ✅</h1>
        <p>If you're reading this, email configuration is working correctly!</p>
        <p>You can now receive notifications from RAG Chatbot.</p>
        """,
        text_body="Test email from RAG Chatbot. Configuration working!"
    )
    
    if success:
        print("✅ Email sent successfully!")
        print(f"Check inbox: {test_email}")
    else:
        print("❌ Failed to send email")
        print("Check your SMTP credentials and try again")

if __name__ == "__main__":
    asyncio.run(test_email())


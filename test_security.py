#!/usr/bin/env python3
"""Test security features."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.security import security_validator

print("=" * 60)
print("SECURITY FEATURE TESTS")
print("=" * 60)

# Test 1: Weak password validation
print("\n1. Testing password strength validation:")
weak_passwords = [
    "password",  # Too weak
    "Password",  # Missing digit and special char
    "Password1",  # Missing special char
    "Password123!",  # Strong password
]

for pwd in weak_passwords:
    result = security_validator.validate_password_strength(pwd)
    status = "✅ PASS" if result["valid"] else "❌ REJECT"
    print(f"   {status}: '{pwd}' - {result['strength']} (score: {result['score']})")
    if not result["valid"]:
        print(f"      Issues: {', '.join(result['issues'])}")

# Test 2: Username validation
print("\n2. Testing username validation:")
test_usernames = [
    ("ab", False),  # Too short
    ("123user", False),  # Starts with number
    ("user-name", True),  # Valid
    ("user_name", True),  # Valid
    ("user@name", False),  # Invalid character
]

for username, expected in test_usernames:
    result = security_validator.validate_username(username)
    status = "✅" if result == expected else "❌"
    print(f"   {status}: '{username}' -> {result} (expected: {expected})")

# Test 3: Email validation
print("\n3. Testing email validation:")
test_emails = [
    ("test@example.com", True),
    ("invalid-email", False),
    ("user@domain", False),
    ("user@domain.co.uk", True),
]

for email, expected in test_emails:
    result = security_validator.validate_email(email)
    status = "✅" if result == expected else "❌"
    print(f"   {status}: '{email}' -> {result} (expected: {expected})")

# Test 4: Filename sanitization
print("\n4. Testing filename sanitization:")
test_filenames = [
    ("../../../etc/passwd", "passwd"),
    ("file<script>.exe", "filescript.exe"),
    ("normal_file.pdf", "normal_file.pdf"),
    ("file with spaces.txt", "file with spaces.txt"),
]

for filename, expected_safe in test_filenames:
    safe = security_validator.sanitize_filename(filename)
    print(f"   '{filename}' -> '{safe}'")

# Test 5: Input sanitization (XSS protection)
print("\n5. Testing input sanitization (XSS protection):")
test_inputs = [
    "<script>alert('xss')</script>",
    "Normal text",
    "<img src=x onerror=alert(1)>",
]

for text in test_inputs:
    sanitized = security_validator.sanitize_input(text)
    print(f"   Input: {text[:50]}")
    print(f"   Sanitized: {sanitized[:50]}")

# Test 6: SQL injection detection
print("\n6. Testing SQL injection detection:")
from backend.security import sql_protection

test_queries = [
    ("SELECT * FROM users", True),  # Should detect
    ("DROP TABLE users;", True),  # Should detect
    ("Normal question about data", False),  # Should pass
    ("'; DELETE FROM users; --", True),  # Should detect
]

for query, should_detect in test_queries:
    detected = sql_protection.check_sql_injection(query)
    status = "✅" if detected == should_detect else "❌"
    print(f"   {status}: '{query[:40]}...' -> detected: {detected}")

print("\n" + "=" * 60)
print("SECURITY TESTS COMPLETE")
print("=" * 60)


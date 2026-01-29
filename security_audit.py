#!/usr/bin/env python3
"""
Security audit script for RAG Chatbot
Checks for common security issues
"""

import os
import sys
from pathlib import Path


class SecurityAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def check_env_file(self):
        """Check if .env contains secrets"""
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                content = f.read()
                
                if 'SECRET_KEY=change-this' in content:
                    self.issues.append("❌ Default SECRET_KEY found in .env")
                else:
                    self.passed.append("✅ SECRET_KEY is customized")
                
                if 'PASSWORD=admin' in content or 'PASSWORD=password' in content:
                    self.issues.append("❌ Weak password found in .env")
                else:
                    self.passed.append("✅ No weak passwords in .env")
        else:
            self.warnings.append("⚠️  .env file not found")
    
    def check_gitignore(self):
        """Check if sensitive files are gitignored"""
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                content = f.read()
                
                checks = {
                    '.env': '.env in .gitignore',
                    'secrets/': 'secrets/ in .gitignore',
                    '*.key': '*.key in .gitignore',
                }
                
                for pattern, desc in checks.items():
                    if pattern in content:
                        self.passed.append(f"✅ {desc}")
                    else:
                        self.issues.append(f"❌ {desc} - MISSING")
        else:
            self.issues.append("❌ .gitignore not found")
    
    def check_file_permissions(self):
        """Check file permissions"""
        sensitive_files = ['secrets', '.env', 'backup.sh']
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                mode = oct(stat.st_mode)[-3:]
                
                if file_path.endswith('/') or os.path.isdir(file_path):
                    # Directory should be 700
                    if mode != '700':
                        self.warnings.append(f"⚠️  {file_path} has permissions {mode} (should be 700)")
                    else:
                        self.passed.append(f"✅ {file_path} has correct permissions (700)")
                else:
                    # File should be 600
                    if mode != '600':
                        self.warnings.append(f"⚠️  {file_path} has permissions {mode} (should be 600)")
                    else:
                        self.passed.append(f"✅ {file_path} has correct permissions (600)")
    
    def check_docker_security(self):
        """Check Docker security"""
        if os.path.exists('docker-compose.yml'):
            with open('docker-compose.yml', 'r') as f:
                content = f.read()
                
                if 'secrets:' in content:
                    self.passed.append("✅ Docker secrets configured")
                else:
                    self.warnings.append("⚠️  Docker secrets not configured")
                
                if 'healthcheck:' in content:
                    self.passed.append("✅ Health checks configured")
                else:
                    self.warnings.append("⚠️  Health checks not configured")
        else:
            self.warnings.append("⚠️  docker-compose.yml not found")
    
    def check_ssl_setup(self):
        """Check SSL configuration"""
        if os.path.exists('nginx/ssl.conf'):
            self.passed.append("✅ SSL configuration exists")
        else:
            self.warnings.append("⚠️  SSL configuration not found (use HTTP for local dev only)")
    
    def run_audit(self):
        """Run all security checks"""
        print("🔍 Running security audit...\n")
        
        self.check_env_file()
        self.check_gitignore()
        self.check_file_permissions()
        self.check_docker_security()
        self.check_ssl_setup()
        
        # Print results
        print("\n" + "="*60)
        print("SECURITY AUDIT RESULTS")
        print("="*60 + "\n")
        
        if self.issues:
            print("🚨 CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        if self.passed:
            print("✅ PASSED:")
            for check in self.passed:
                print(f"  {check}")
            print()
        
        # Summary
        total = len(self.issues) + len(self.warnings) + len(self.passed)
        score = ((len(self.passed) / total) * 100) if total > 0 else 0
        
        print("="*60)
        print(f"SCORE: {score:.1f}%")
        print(f"Passed: {len(self.passed)} | Warnings: {len(self.warnings)} | Issues: {len(self.issues)}")
        print("="*60)
        
        # Exit code
        if self.issues:
            print("\n❌ Security audit FAILED - fix critical issues!")
            sys.exit(1)
        elif self.warnings:
            print("\n⚠️  Security audit PASSED with warnings")
            sys.exit(0)
        else:
            print("\n✅ Security audit PASSED!")
            sys.exit(0)


if __name__ == "__main__":
    auditor = SecurityAuditor()
    auditor.run_audit()


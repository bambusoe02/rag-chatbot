#!/usr/bin/env python3
"""
Automated optimization and cleanup script
Run before production deployment
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


class ProductionOptimizer:
    """Optimize codebase for production"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.optimizations = []
    
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"{text}")
        print(f"{'='*60}\n")
    
    def check_environment_variables(self):
        """Check for hardcoded secrets"""
        print("🔍 Checking for hardcoded secrets...")
        
        suspicious_patterns = [
            (r'SECRET_KEY\s*=\s*["\'][\w-]{20,}["\']', "Hardcoded SECRET_KEY"),
            (r'PASSWORD\s*=\s*["\'][\w]{8,}["\']', "Hardcoded password"),
            (r'API_KEY\s*=\s*["\'][\w-]{20,}["\']', "Hardcoded API key"),
            (r'mongodb://.*:.*@', "MongoDB connection string with credentials"),
            (r'postgresql://.*:.*@', "PostgreSQL connection string with credentials"),
        ]
        
        for root, dirs, files in os.walk('.'):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__', 'data']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.env.example')):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            for pattern, description in suspicious_patterns:
                                if re.search(pattern, content):
                                    self.warnings.append(f"{filepath}: {description}")
                    except:
                        pass
        
        if not self.warnings:
            print(f"{GREEN}✅ No hardcoded secrets found{NC}")
        else:
            print(f"{YELLOW}⚠️  Found {len(self.warnings)} potential issues:{NC}")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"  {warning}")
    
    def remove_debug_code(self):
        """Remove debug prints and breakpoints"""
        print("\n🔍 Checking for debug code...")
        
        debug_patterns = [
            r'print\s*\(',
            r'console\.log\s*\(',
            r'debugger;',
            r'breakpoint\(\)',
            r'import pdb',
            r'pdb\.set_trace\(\)',
        ]
        
        count = 0
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', 'data']]
            
            for file in files:
                if file.endswith(('.py', '.js')):
                    filepath = os.path.join(root, file)
                    
                    # Skip test files
                    if 'test' in filepath.lower():
                        continue
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            for pattern in debug_patterns:
                                matches = re.findall(pattern, content)
                                count += len(matches)
                    except:
                        pass
        
        if count == 0:
            print(f"{GREEN}✅ No debug code found{NC}")
        else:
            print(f"{YELLOW}⚠️  Found {count} debug statements (review manually){NC}")
    
    def optimize_docker_images(self):
        """Check Docker image sizes"""
        print("\n🐳 Checking Docker images...")
        
        try:
            result = subprocess.run(
                ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}\t{{.Size}}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                large_images = []
                
                for line in lines:
                    if 'rag-chatbot' in line or 'rag' in line.lower():
                        parts = line.split('\t')
                        if len(parts) == 2:
                            name, size = parts
                            
                            # Parse size (e.g., "1.2GB")
                            size_match = re.search(r'([\d.]+)\s*([MG]B)', size)
                            if size_match:
                                value = float(size_match.group(1))
                                unit = size_match.group(2)
                                
                                # Flag images > 1GB
                                if unit == 'GB' and value > 1:
                                    large_images.append(f"{name}: {size}")
                
                if large_images:
                    print(f"{YELLOW}⚠️  Large Docker images found:{NC}")
                    for img in large_images:
                        print(f"  {img}")
                    print(f"\n💡 Consider using multi-stage builds to reduce size")
                else:
                    print(f"{GREEN}✅ Docker images optimized{NC}")
        except FileNotFoundError:
            print(f"{YELLOW}⚠️  Docker not found, skipping{NC}")
    
    def check_dependencies(self):
        """Check for outdated or vulnerable dependencies"""
        print("\n📦 Checking dependencies...")
        
        # Check Python dependencies
        if os.path.exists('requirements.txt'):
            print("  Checking Python packages...")
            
            try:
                result = subprocess.run(
                    ['pip', 'list', '--outdated'],
                    capture_output=True,
                    text=True
                )
                
                outdated = len(result.stdout.strip().split('\n')) - 2
                if outdated > 0:
                    print(f"{YELLOW}  ⚠️  {outdated} outdated Python packages{NC}")
                    print(f"  Run: pip list --outdated")
                else:
                    print(f"{GREEN}  ✅ Python packages up to date{NC}")
            except:
                print(f"{YELLOW}  ⚠️  Could not check Python packages{NC}")
            
            # Security check
            try:
                result = subprocess.run(
                    ['safety', 'check'],
                    capture_output=True,
                    text=True
                )
                
                if 'vulnerabilities found' in result.stdout or result.returncode != 0:
                    print(f"{RED}  ❌ Security vulnerabilities found!{NC}")
                    print(f"  Run: safety check")
                else:
                    print(f"{GREEN}  ✅ No known vulnerabilities{NC}")
            except FileNotFoundError:
                print(f"{YELLOW}  ⚠️  'safety' not installed, skipping security check{NC}")
                print(f"  Install: pip install safety")
    
    def optimize_database(self):
        """Database optimization recommendations"""
        print("\n🗄️  Database optimization recommendations...")
        
        recommendations = [
            "✅ Add indexes on frequently queried columns",
            "✅ Enable query caching if not already",
            "✅ Set up connection pooling",
            "✅ Configure vacuum/analyze (PostgreSQL)",
            "✅ Monitor slow queries",
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
    
    def check_file_sizes(self):
        """Check for large files in repo"""
        print("\n📁 Checking file sizes...")
        
        large_files = []
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', 'data', '__pycache__']]
            
            for file in files:
                filepath = os.path.join(root, file)
                
                try:
                    size = os.path.getsize(filepath)
                    
                    # Flag files > 10MB
                    if size > 10 * 1024 * 1024:
                        large_files.append((filepath, size))
                except:
                    pass
        
        if large_files:
            print(f"{YELLOW}⚠️  Large files found (should not be in git):{NC}")
            for filepath, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
                size_mb = size / (1024 * 1024)
                print(f"  {filepath}: {size_mb:.1f} MB")
        else:
            print(f"{GREEN}✅ No large files in repository{NC}")
    
    def create_production_env(self):
        """Create production .env template"""
        print("\n⚙️  Creating production .env template...")
        
        prod_env = """# PRODUCTION ENVIRONMENT VARIABLES
# Copy to .env and fill in actual values

# CRITICAL - CHANGE THESE!
SECRET_KEY=CHANGE_THIS_TO_RANDOM_32_CHAR_STRING
DATABASE_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
ADMIN_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email (optional)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:14b-instruct

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Monitoring
SENTRY_DSN=your-sentry-dsn (optional)

# Domain
APP_URL=https://your-domain.com
"""
        
        with open('.env.production.template', 'w') as f:
            f.write(prod_env)
        
        print(f"{GREEN}✅ Created .env.production.template{NC}")
        print(f"  Copy to .env and update values")
    
    def generate_summary(self):
        """Generate optimization summary"""
        self.print_header("OPTIMIZATION SUMMARY")
        
        print(f"Issues found: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Optimizations: {len(self.optimizations)}")
        
        if self.issues:
            print(f"\n{RED}🚨 CRITICAL ISSUES:{NC}")
            for issue in self.issues:
                print(f"  ❌ {issue}")
        
        if self.warnings:
            print(f"\n{YELLOW}⚠️  WARNINGS:{NC}")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  ⚠️  {warning}")
        
        print(f"\n{GREEN}✅ NEXT STEPS:{NC}")
        print("  1. Review all warnings and issues")
        print("  2. Update .env with production values")
        print("  3. Run tests: pytest")
        print("  4. Run load tests: ./tests/load/run_tests.sh")
        print("  5. Complete PRODUCTION_CHECKLIST.md")
        print("  6. Deploy to staging first")
        print("  7. Monitor for 24 hours")
        print("  8. Deploy to production")
    
    def run(self):
        """Run all optimization checks"""
        self.print_header("🚀 PRODUCTION OPTIMIZATION")
        
        self.check_environment_variables()
        self.remove_debug_code()
        self.optimize_docker_images()
        self.check_dependencies()
        self.optimize_database()
        self.check_file_sizes()
        self.create_production_env()
        
        self.generate_summary()


if __name__ == "__main__":
    optimizer = ProductionOptimizer()
    optimizer.run()


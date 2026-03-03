#!/usr/bin/env python3
"""
Email Service Diagnostic Tool for app
Tests email configuration and connectivity without requiring the web interface.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.email_utils import test_email_connection, send_email
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60)

def print_section(text):
    """Print a formatted section"""
    print("\n" + text)
    print("-" * len(text))

def main():
    """Main diagnostic flow"""
    print_header("app Email Service Diagnostic")
    
    # Test 1: Check configuration
    print_section("Step 1: Checking Email Configuration")
    email = os.getenv("EMAIL_ADDRESS", "").strip()
    password = os.getenv("EMAIL_PASSWORD", "").strip()
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "465")
    
    print(f"Email Address: {email if email else '❌ NOT SET'}")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    
    if password == "your_app_password_here" or not password:
        print(f"Password: ❌ NOT SET or using placeholder")
        print("\n⚠️  ERROR: Email password not configured!")
        print("\nTo fix this:")
        print("1. Open your .env file")
        print("2. For Gmail:")
        print("   - Go to: https://myaccount.google.com/apppasswords")
        print("   - Create an 'App password' for your app")
        print("   - Copy the 16-character password")
        print("   - Set: EMAIL_PASSWORD=<your_16_char_password>")
        print("3. Or use an app-specific password from your email provider")
        return False
    
    print(f"Password: ✓ Configured")
    
    # Test 2: Connection test
    print_section("Step 2: Testing Email Service Configuration")
    result = test_email_connection()
    
    if result['connection_test'] and result['auth_test']:
        print("✓ Email service is properly configured and working!")
        return True
    else:
        print("❌ Email service test failed")
        if not result['connection_test']:
            print(f"\nCannot connect to {smtp_server}:{smtp_port}")
            print("Possible causes:")
            print("  - Network connection issue")
            print("  - Wrong SMTP server address")
            print("  - Firewall blocking the connection")
        
        if not result['auth_test']:
            print("\n❌ Authentication failed")
            print("Possible causes:")
            print("  - Invalid email address")
            print("  - Invalid or expired app password")
            print("  - 2FA enabled without app password")
        
        print(f"\nError: {result.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    print("\n")
    success = main()
    
    if success:
        print_section("Next Steps")
        print("✓ Your email service is ready!")
        print("\nYou can now:")
        print("  - Go to /preferences in your app dashboard")
        print("  - Enable 'Email Alerts'")
        print("  - Expiry items will send you email notifications")
    
    print("\n")
    sys.exit(0 if success else 1)

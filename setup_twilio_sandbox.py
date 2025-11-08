#!/usr/bin/env python3
"""
Interactive Twilio Sandbox Setup Script
Helps configure .env file for WhatsApp testing
"""
import os
import sys
from pathlib import Path


def print_header():
    print("\n" + "="*70)
    print("🚀 Twilio WhatsApp Sandbox Setup")
    print("="*70 + "\n")


def print_step(step_num, title):
    print(f"\n{'─'*70}")
    print(f"📋 Step {step_num}: {title}")
    print("─"*70 + "\n")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("❌ This field is required. Please enter a value.")


def validate_phone(phone):
    """Validate phone number format"""
    if not phone.startswith('whatsapp:+'):
        return False
    # Remove prefix and check if remaining is digits
    number = phone.replace('whatsapp:+', '')
    return number.isdigit() and len(number) >= 10


def setup_sandbox():
    """Interactive setup process"""
    print_header()
    
    print("This script will help you configure Twilio WhatsApp Sandbox for testing.")
    print("\n📖 Before you begin:")
    print("   1. Create a Twilio account: https://www.twilio.com/try-twilio")
    print("   2. Join the sandbox from WhatsApp: Send 'join your-code' to +1 (415) 523-8886")
    print("   3. Have your Account SID and Auth Token ready")
    print("\n")
    
    ready = input("Ready to continue? (y/n): ").lower()
    if ready != 'y':
        print("\n👋 No problem! Come back when you're ready.")
        print("📚 Read the full guide: TWILIO_SANDBOX_SETUP.md")
        return False
    
    # Step 1: Get Twilio credentials
    print_step(1, "Twilio Account Credentials")
    print("Get these from: https://console.twilio.com")
    print("(Found on your Dashboard under 'Account Info')\n")
    
    account_sid = get_input("Enter your Twilio Account SID")
    if not account_sid.startswith('AC'):
        print("⚠️  Warning: Account SID usually starts with 'AC'")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Setup cancelled")
            return False
    
    auth_token = get_input("Enter your Twilio Auth Token")
    if len(auth_token) < 20:
        print("⚠️  Warning: Auth Token seems too short")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Setup cancelled")
            return False
    
    # Step 2: Confirm sandbox join
    print_step(2, "Sandbox Verification")
    print("Have you joined the Twilio sandbox from WhatsApp?")
    print("(You should have sent 'join your-code' to +1 (415) 523-8886)\n")
    
    joined = input("Have you joined the sandbox? (y/n): ").lower()
    if joined != 'y':
        print("\n❌ Please join the sandbox first!")
        print("\n📱 To join:")
        print("   1. Open WhatsApp on your phone")
        print("   2. Start chat with: +1 (415) 523-8886")
        print("   3. Send message: join <your-code>")
        print("   4. Get your code from: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        print("\nRun this script again after joining!")
        return False
    
    # Step 3: Get phone number
    print_step(3, "Your WhatsApp Number")
    print("Enter your WhatsApp number (the one you used to join sandbox)")
    print("Format: whatsapp:+countrycode+number")
    print("Example: whatsapp:+12025551234\n")
    
    while True:
        to_number = get_input("Your WhatsApp number")
        
        # Auto-add prefix if missing
        if not to_number.startswith('whatsapp:'):
            if to_number.startswith('+'):
                to_number = f"whatsapp:{to_number}"
            else:
                to_number = f"whatsapp:+{to_number}"
        
        if validate_phone(to_number):
            break
        else:
            print("❌ Invalid format. Please use: whatsapp:+countrycode+number")
            print("   Example: whatsapp:+12025551234")
    
    # Step 4: Confirm configuration
    print_step(4, "Review Configuration")
    print(f"Account SID:  {account_sid[:10]}...{account_sid[-4:]}")
    print(f"Auth Token:   {auth_token[:10]}...{auth_token[-4:]}")
    print(f"From Number:  whatsapp:+14155238886 (Sandbox)")
    print(f"To Number:    {to_number}")
    print()
    
    confirm = input("Save this configuration? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Setup cancelled")
        return False
    
    # Step 5: Save to .env
    print_step(5, "Saving Configuration")
    
    env_path = Path(__file__).parent / '.env'
    
    # Read existing .env if it exists
    existing_lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            existing_lines = f.readlines()
    
    # Remove old Twilio sandbox variables
    new_lines = []
    twilio_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN', 
        'TWILIO_WHATSAPP_FROM_SANDBOX',
        'TWILIO_WHATSAPP_TO_SANDBOX'
    ]
    
    for line in existing_lines:
        # Keep line if it doesn't start with any Twilio sandbox variable
        if not any(line.startswith(f"{var}=") for var in twilio_vars):
            new_lines.append(line)
    
    # Add new configuration
    sandbox_config = f"""
# Twilio Sandbox Configuration (added by setup script)
TWILIO_ACCOUNT_SID={account_sid}
TWILIO_AUTH_TOKEN={auth_token}
TWILIO_WHATSAPP_FROM_SANDBOX=whatsapp:+14155238886
TWILIO_WHATSAPP_TO_SANDBOX={to_number}
"""
    
    # Write to .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        f.write(sandbox_config)
    
    print(f"✅ Configuration saved to: {env_path}")
    
    # Step 6: Test
    print_step(6, "Test Your Setup")
    print("Configuration complete! Now let's test it.\n")
    
    test_now = input("Run test now? (y/n): ").lower()
    if test_now == 'y':
        print("\n" + "="*70)
        print("🧪 Running WhatsApp notification test...")
        print("="*70 + "\n")
        
        # Run test script
        os.system("python test_whatsapp_news_notification.py")
    else:
        print("\n✅ Setup complete!")
        print("\n🧪 To test manually, run:")
        print("   python test_whatsapp_news_notification.py")
    
    print("\n" + "="*70)
    print("📚 For more information, see: TWILIO_SANDBOX_SETUP.md")
    print("="*70 + "\n")
    
    return True


def main():
    try:
        success = setup_sandbox()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

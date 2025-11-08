#!/usr/bin/env python3
"""
WhatsApp Configuration Helper
Helps you set up and test WhatsApp notifications
"""
import os
import sys
from dotenv import load_dotenv, set_key

load_dotenv()


def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def print_status():
    """Print current WhatsApp configuration status"""
    print_header("Current WhatsApp Configuration")
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_FROM')
    to_number = os.getenv('TWILIO_WHATSAPP_TO')
    
    print(f"Account SID: {account_sid[:20]}..." if account_sid else "❌ Not set")
    print(f"Auth Token:  {auth_token[:20]}..." if auth_token else "❌ Not set")
    print(f"From Number: {from_number}" if from_number else "❌ Not set")
    print(f"To Number:   {to_number}" if to_number else "❌ Not set")
    
    # Detect mode
    if from_number:
        if '+14155238886' in from_number:
            print("\n📱 Mode: SANDBOX (Testing)")
            print("   ⚠️  Limited to 50 messages/day")
            print("   ⚠️  Need to rejoin every 3 days")
        else:
            print("\n📱 Mode: PRODUCTION")
            print("   ✅ Requires WhatsApp Message Templates")
            print("   ✅ No daily message limits")
    
    print()


def switch_to_sandbox():
    """Switch to Twilio sandbox number"""
    print_header("Switching to Sandbox Mode")
    
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ Error: .env file not found")
        return
    
    set_key(env_file, 'TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    
    print("✅ Switched to sandbox number: +14155238886")
    print("\n📝 Next steps:")
    print("   1. Text 'join <code>' to +14155238886")
    print("   2. Get code from: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print("   3. Run: python3 test_whatsapp_notifications.py")
    print()


def switch_to_production(number=None):
    """Switch to production number"""
    print_header("Switching to Production Mode")
    
    if not number:
        number = input("Enter your production WhatsApp number (e.g., +15558419388): ").strip()
    
    if not number.startswith('+'):
        number = '+' + number
    
    env_file = '.env'
    if not os.path.exists(env_file):
        print("❌ Error: .env file not found")
        return
    
    whatsapp_number = f'whatsapp:{number}'
    set_key(env_file, 'TWILIO_WHATSAPP_FROM', whatsapp_number)
    
    print(f"✅ Switched to production number: {number}")
    print("\n⚠️  Important: You need WhatsApp Message Templates!")
    print("   See: WHATSAPP_TEMPLATE_SETUP.md for setup instructions")
    print()


def test_connection():
    """Test WhatsApp connection"""
    print_header("Testing WhatsApp Connection")
    print("Running test script...\n")
    
    import subprocess
    result = subprocess.run(['python3', 'test_whatsapp_notifications.py'])
    
    if result.returncode == 0:
        print("\n✅ Test completed - check your WhatsApp for messages")
    else:
        print("\n❌ Test failed - check logs for details")
    print()


def show_menu():
    """Show interactive menu"""
    while True:
        print_header("WhatsApp Setup Helper")
        print("1. Show current configuration")
        print("2. Switch to Sandbox mode (for testing)")
        print("3. Switch to Production mode (requires templates)")
        print("4. Test WhatsApp connection")
        print("5. View setup guide")
        print("6. Exit")
        print()
        
        choice = input("Select option (1-6): ").strip()
        
        if choice == '1':
            print_status()
        elif choice == '2':
            switch_to_sandbox()
        elif choice == '3':
            switch_to_production()
        elif choice == '4':
            test_connection()
        elif choice == '5':
            print("\n📖 Opening setup guide...")
            os.system('cat WHATSAPP_TEMPLATE_SETUP.md | less')
        elif choice == '6':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("❌ Invalid option\n")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd == 'status':
            print_status()
        elif cmd == 'sandbox':
            switch_to_sandbox()
        elif cmd == 'production':
            number = sys.argv[2] if len(sys.argv) > 2 else None
            switch_to_production(number)
        elif cmd == 'test':
            test_connection()
        else:
            print("Usage: python3 setup_whatsapp.py [status|sandbox|production|test]")
            print("   or: python3 setup_whatsapp.py (for interactive menu)")
    else:
        show_menu()


if __name__ == '__main__':
    main()

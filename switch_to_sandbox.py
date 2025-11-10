#!/usr/bin/env python3
"""
Switch WhatsApp configuration to use Sandbox (for testing)
"""
import os
from dotenv import load_dotenv, set_key

load_dotenv()

env_file = '.env'

print("\n" + "="*70)
print("  Switching to Twilio WhatsApp Sandbox")
print("="*70 + "\n")

# Get current config
current_from = os.getenv('TWILIO_WHATSAPP_FROM')
sandbox_from = os.getenv('TWILIO_WHATSAPP_FROM_SANDBOX', 'whatsapp:+14155238886')

print(f"Current: {current_from}")
print(f"Sandbox: {sandbox_from}")
print()

if current_from == sandbox_from:
    print("✅ Already using sandbox!")
else:
    # Update .env
    set_key(env_file, 'TWILIO_WHATSAPP_FROM', sandbox_from)
    print("✅ Switched to sandbox!")
    print()
    print(f"Updated TWILIO_WHATSAPP_FROM to: {sandbox_from}")

print()
print("="*70)
print()
print("Next steps:")
print()
print("1. Make sure you're connected to sandbox:")
print("   - Open WhatsApp")
print("   - Send 'join <your-code>' to +14155238886")
print()
print("2. Find your code:")
print("   python3 get_sandbox_code.py")
print()
print("3. Test the template:")
print("   python3 send_deep_analysis_production.py")
print()

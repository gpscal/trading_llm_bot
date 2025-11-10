#!/usr/bin/env python3
"""
Get your Twilio WhatsApp Sandbox join code
"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

print("\n" + "="*70)
print("  Twilio WhatsApp Sandbox - Getting Your Join Code")
print("="*70 + "\n")

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

try:
    # Get sandbox configuration
    # Note: Twilio doesn't have a direct API to get sandbox join code
    # But we can check if messages work and provide instructions
    
    print("To find your Twilio WhatsApp Sandbox join code:")
    print()
    print("Option 1: Check Twilio Console (Easiest)")
    print("  1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
    print("  2. Look for 'Your Sandbox' section")
    print("  3. You'll see: 'join <your-code>' (e.g., 'join happy-tiger')")
    print()
    print("Option 2: Check Previous Messages")
    print("  - Check if you have any messages from +14155238886 in your WhatsApp")
    print("  - The first message should have told you the join code")
    print()
    print("="*70)
    print()
    print("After you find the code:")
    print()
    print("1. Open WhatsApp on your phone")
    print("2. Send a message to: +14155238886")
    print("3. Message: join <your-code>")
    print("   (Replace <your-code> with the actual code, e.g., 'join happy-tiger')")
    print()
    print("4. You will receive a confirmation message from Twilio")
    print()
    print("5. Run this test: python3 send_deep_analysis_production.py")
    print()
    print("Note: Sandbox connection expires every 3 days, then you need to rejoin")
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()

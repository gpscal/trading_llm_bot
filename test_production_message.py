#!/usr/bin/env python3
"""
Test sending message to production WhatsApp number
This will help us understand if we can send messages and open the 24-hour window
"""
import os
import sys
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
from_number = os.getenv('TWILIO_WHATSAPP_FROM')
to_number = os.getenv('TWILIO_WHATSAPP_TO')

print("\n" + "="*70)
print("  Testing Production WhatsApp Number")
print("="*70 + "\n")

print(f"From: {from_number} (Production)")
print(f"To: {to_number}")
print()

# Step 1: Check if we're already in 24-hour window
print("Step 1: Testing freeform message (checks if 24-hour window is active)...")
print()

try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        body="🤖 *Trading Bot Test*\n\nTesting production WhatsApp connection."
    )
    print(f"✅ Message sent! SID: {msg.sid}")
    print(f"   Initial status: {msg.status}")
    print()
    print("📱 Check your WhatsApp for the message!")
    print()
    print("If you receive it, this means the 24-hour window is active.")
    print("You can now send template messages for the next 24 hours.")
    sys.exit(0)
    
except Exception as e:
    error_str = str(e)
    print(f"❌ Message blocked: {e}")
    print()
    
    if '63016' in error_str:
        print("="*70)
        print("  ERROR 63016: Outside 24-Hour Messaging Window")
        print("="*70)
        print()
        print("WhatsApp requires users to message your bot FIRST before you")
        print("can send them messages (unless using approved templates).")
        print()
        print("To fix this:")
        print()
        print("Option 1: MESSAGE YOUR BOT (Recommended)")
        print(f"  1. Open WhatsApp on your phone")
        print(f"  2. Send a message to: {from_number}")
        print(f"  3. Message can be anything: 'Hi', 'Test', etc.")
        print(f"  4. Wait 5 seconds")
        print(f"  5. Run this script again: python3 test_production_message.py")
        print()
        print("Option 2: FIX THE TEMPLATE")
        print("  The template has an API error that needs Twilio support")
        print("  to debug. Template mode would bypass the 24-hour window.")
        print()
        
    elif '21656' in error_str or '21617' in error_str:
        print("="*70)
        print("  Phone Number Issue")
        print("="*70)
        print()
        print(f"The number {to_number} may not be:")
        print("  - Registered with WhatsApp")
        print("  - Able to receive WhatsApp messages")
        print("  - Formatted correctly")
        print()
        print("Please verify:")
        print("  1. The number is active on WhatsApp")
        print("  2. The number format in .env is correct")
        print(f"     Current: TWILIO_WHATSAPP_TO={to_number}")
        print()
        
    else:
        print("Unknown error. Check Twilio console for details:")
        print("https://console.twilio.com/us1/monitor/logs/errors")
        
    sys.exit(1)

#!/usr/bin/env python3
"""
Debug script to test Twilio Content Template variable format
"""
import os
import json
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Initialize Twilio client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_WHATSAPP_FROM')
to_number = os.getenv('TWILIO_WHATSAPP_TO')

client = Client(account_sid, auth_token)

content_sid = "HXa150023aee81063cc8dc9cb944507283"

print("Testing Twilio Content Template Variable Formats")
print("="*70)
print()

# Test 1: Simple JSON format (recommended by Twilio docs)
print("Test 1: Simple key-value JSON")
variables = {
    "1": "BTC",
    "2": "75,420.00",
    "3": "2025-11-10 12:00:00"
}

print(f"Variables: {json.dumps(variables, indent=2)}")
print()

try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=content_sid,
        content_variables=json.dumps(variables)
    )
    print(f"✅ Test 1 SUCCESS! Message SID: {msg.sid}")
    print("   The simple JSON format works!")
except Exception as e:
    print(f"❌ Test 1 FAILED: {e}")

print()
print("="*70)

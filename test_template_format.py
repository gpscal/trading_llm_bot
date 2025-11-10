#!/usr/bin/env python3
"""
Test different variable formats for Twilio Content API
"""
import os
import json
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

content_sid = "HXa150023aee81063cc8dc9cb944507283"
from_number = os.getenv('TWILIO_WHATSAPP_FROM')
to_number = os.getenv('TWILIO_WHATSAPP_TO')

print("Testing different Content Variable formats")
print("="*70)
print()

# Short test variables
variables_dict = {
    "1": "BTC",
    "2": "75420",
    "3": "2025-11-10"
}

# Format 1: JSON string (what we've been trying)
print("Format 1: JSON string")
print(f"  {json.dumps(variables_dict)}")
try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=content_sid,
        content_variables=json.dumps(variables_dict)
    )
    print(f"  ✅ SUCCESS! SID: {msg.sid}\n")
except Exception as e:
    print(f"  ❌ FAILED: {str(e)[:100]}\n")

# Format 2: Pass dict directly (let Twilio SDK handle it)
print("Format 2: Dict directly (no JSON)")
try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=content_sid,
        content_variables=variables_dict
    )
    print(f"  ✅ SUCCESS! SID: {msg.sid}\n")
except Exception as e:
    print(f"  ❌ FAILED: {str(e)[:100]}\n")

# Format 3: Try as string representation
print("Format 3: String representation")
try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=content_sid,
        content_variables=str(variables_dict)
    )
    print(f"  ✅ SUCCESS! SID: {msg.sid}\n")
except Exception as e:
    print(f"  ❌ FAILED: {str(e)[:100]}\n")

print("="*70)
print("\nNote: If all fail, the template might need to be re-approved")
print("or the Content SID might be for a different template version.")

#!/usr/bin/env python3
"""
Test with minimal variables to debug the format issue
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

print("Testing minimal variables to debug format...")
print("="*70)
print()

# First, let's fetch the template to see what Twilio has
print("Fetching template from Twilio...")
try:
    content = client.content.v1.contents(content_sid).fetch()
    print(f"✅ Template found: {content.friendly_name}")
    print(f"   Type: {content.types}")
    print()
    
    # Check the template structure
    if hasattr(content, 'types') and content.types:
        template_type = content.types.get('twilio/text', {})
        if 'body' in template_type:
            body = template_type['body']
            print(f"Template body: {body[:200]}...")
            print()
    
except Exception as e:
    print(f"❌ Error fetching template: {e}")
    print()

# Try sending with just 3 variables
print("Attempting to send with first 3 variables only...")
variables = {
    "1": "BTC",
    "2": "75420",
    "3": "2025-11-10 12:00"
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
    print(f"✅ SUCCESS! Message SID: {msg.sid}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    # Try to get more details
    error_str = str(e)
    if "20" in error_str:  # Twilio error codes
        print("This is a Twilio error. Check:")
        print("1. Content SID is correct")
        print("2. Template has the expected variable placeholders")
        print("3. All required variables are provided")

print()
print("="*70)

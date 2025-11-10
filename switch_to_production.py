#!/usr/bin/env python3
"""
Switch WhatsApp configuration to use Production number
(Only use this after WhatsApp is enabled on your number)
"""
import os
from dotenv import load_dotenv, set_key

load_dotenv()

env_file = '.env'

print("\n" + "="*70)
print("  Switching to Production WhatsApp Number")
print("="*70 + "\n")

print("⚠️  WARNING: Only use this after:")
print("  1. You've applied for WhatsApp Business API")
print("  2. Facebook/WhatsApp approved your business")
print("  3. WhatsApp is enabled on your number")
print()

response = input("Have you completed WhatsApp setup on your number? (yes/no): ").lower()

if response != 'yes':
    print()
    print("❌ Please complete WhatsApp setup first!")
    print()
    print("See: ENABLE_WHATSAPP_ON_YOUR_NUMBER.md for instructions")
    print()
    print("Use sandbox for now: python3 switch_to_sandbox.py")
    exit(1)

print()
print("Enter your WhatsApp-enabled number (e.g., +19129133993):")
production_number = input("Number: ").strip()

if not production_number.startswith('+'):
    production_number = '+' + production_number

production_whatsapp = f'whatsapp:{production_number}'

print()
print(f"Setting production number to: {production_whatsapp}")
print()

confirm = input("Confirm? (yes/no): ").lower()

if confirm == 'yes':
    set_key(env_file, 'TWILIO_WHATSAPP_FROM', production_whatsapp)
    print()
    print("✅ Switched to production number!")
    print()
    print(f"TWILIO_WHATSAPP_FROM = {production_whatsapp}")
    print()
    print("Test it:")
    print("  python3 send_deep_analysis_production.py")
    print()
else:
    print()
    print("❌ Cancelled. No changes made.")
    print()

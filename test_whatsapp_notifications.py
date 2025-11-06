#!/usr/bin/env python3
"""
Test WhatsApp notifications
Run this script to verify WhatsApp integration is working
"""
import os
import asyncio
from dotenv import load_dotenv
from utils.whatsapp_notifier import get_whatsapp_notifier

# Load environment variables from .env file
load_dotenv()


def test_whatsapp():
    """Test WhatsApp notification system"""
    print("?? Testing WhatsApp notification system...")
    print("=" * 50)
    
    # Initialize notifier
    notifier = get_whatsapp_notifier()
    
    if not notifier.enabled:
        print("? WhatsApp notifier is not enabled!")
        print("\nPlease configure the following in your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886")
        print("  TWILIO_WHATSAPP_TO=whatsapp:+1234567890")
        print("\nTo get these credentials:")
        print("  1. Sign up at https://www.twilio.com/")
        print("  2. Go to Console > WhatsApp > Senders")
        print("  3. Get your Account SID and Auth Token from dashboard")
        print("  4. Use Twilio's sandbox number as FROM")
        print("  5. Join the sandbox by texting the code to the number")
        return False
    
    print("? WhatsApp notifier is configured")
    print(f"   From: {notifier.from_number}")
    print(f"   To: {notifier.to_number}")
    print()
    
    # Test connection
    print("?? Sending test message...")
    if notifier.test_connection():
        print("? Test message sent successfully!")
        print()
        
        # Test signal alert
        print("?? Sending signal change alert...")
        success = notifier.send_signal_change_alert(
            coin='BTC',
            old_signal='HOLD',
            new_signal='BUY',
            price=75000.00,
            confidence=0.85,
            llm_signal={
                'signal': 'BUY',
                'confidence': 'HIGH',
                'confidence_score': 0.9,
                'reasoning': 'Strong bullish momentum with positive technical indicators. RSI showing oversold conditions with potential reversal.',
                'stop_loss': 73000.00,
                'take_profit': 78000.00
            }
        )
        
        if success:
            print("? Signal alert sent successfully!")
        else:
            print("? Failed to send signal alert")
        
        print()
        print("=" * 50)
        print("? WhatsApp integration test complete!")
        print("Check your WhatsApp for the test messages.")
        return True
    else:
        print("? Failed to send test message")
        print("Please check your Twilio credentials and WhatsApp setup")
        return False


if __name__ == '__main__':
    test_whatsapp()

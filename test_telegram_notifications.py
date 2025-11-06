#!/usr/bin/env python3
"""
Test script for Telegram notifications
Tests bot connection and sends sample notifications
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.telegram_notifier import get_telegram_notifier
from utils.signal_tracker import get_signal_tracker


async def test_telegram():
    """Test Telegram bot integration"""
    
    print("=" * 60)
    print("TELEGRAM BOT NOTIFICATION TEST")
    print("=" * 60)
    
    # Initialize notifier
    telegram = get_telegram_notifier()
    
    if not telegram.enabled:
        print("\n? Telegram not configured!")
        print("\nPlease set the following in your .env file:")
        print("  TELEGRAM_API=your_bot_token_here")
        print("  TELEGRAM_CHAT_ID=your_chat_id_here")
        print("\nTo get your bot token:")
        print("  1. Message @BotFather on Telegram")
        print("  2. Send /newbot and follow instructions")
        print("  3. Copy the bot token")
        print("\nTo get your chat ID:")
        print("  1. Message your bot (any message)")
        print("  2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("  3. Look for 'chat':{'id': YOUR_CHAT_ID}")
        return False
    
    print(f"\n? Telegram configured")
    print(f"  Bot Token: {telegram.bot_token[:20]}...")
    print(f"  Chat ID: {telegram.chat_id}")
    
    # Test 1: Connection test
    print("\n" + "=" * 60)
    print("TEST 1: Bot Connection")
    print("=" * 60)
    
    success = await telegram.test_connection()
    if success:
        print("? Connection successful - check your Telegram for test message")
    else:
        print("? Connection failed - check your bot token and chat ID")
        return False
    
    # Test 2: Signal change notification
    print("\n" + "=" * 60)
    print("TEST 2: Signal Change Notification")
    print("=" * 60)
    
    llm_signal = {
        'signal': 'BUY',
        'confidence': 'HIGH',
        'confidence_score': 0.85,
        'reasoning': 'Strong bullish momentum detected. RSI shows oversold conditions recovering, MACD crossed above signal line, and volume is increasing. Technical indicators align for upward movement.',
        'stop_loss': 95000.0,
        'take_profit': 102000.0
    }
    
    deep_analysis = {
        'signal': 'BUY',
        'confidence_score': 0.78,
        'summary': 'Market showing strong accumulation patterns. Institutional buying pressure evident. Key support levels holding firm.',
        'recommended_action': 'BUY'
    }
    
    success = telegram.send_signal_change_alert(
        coin='BTC',
        old_signal='HOLD',
        new_signal='BUY',
        price=98500.50,
        confidence=0.82,
        llm_signal=llm_signal,
        deep_analysis=deep_analysis
    )
    
    if success:
        print("? Signal change notification sent - check your Telegram")
    else:
        print("? Failed to send signal change notification")
    
    # Test 3: Trade execution notification
    print("\n" + "=" * 60)
    print("TEST 3: Trade Execution Notification")
    print("=" * 60)
    
    success = telegram.send_trade_execution_alert(
        coin='BTC',
        action='BUY',
        amount=0.015,
        price=98500.50,
        total_value=1477.51,
        balance_usdt=8522.49,
        balance_coin=0.015
    )
    
    if success:
        print("? Trade execution notification sent - check your Telegram")
    else:
        print("? Failed to send trade execution notification")
    
    # Test 4: Signal tracker
    print("\n" + "=" * 60)
    print("TEST 4: Signal Tracker")
    print("=" * 60)
    
    tracker = get_signal_tracker()
    
    # Simulate signal changes
    print("\nSimulating signal changes...")
    
    changed, old = tracker.check_signal_change('BTC', 'HOLD')
    print(f"  First check: Changed={changed}, Old={old}")
    
    changed, old = tracker.check_signal_change('BTC', 'HOLD')
    print(f"  Second check (same): Changed={changed}, Old={old}")
    
    changed, old = tracker.check_signal_change('BTC', 'BUY')
    print(f"  Third check (changed): Changed={changed}, Old={old}")
    
    if changed and old == 'HOLD':
        print("? Signal tracker working correctly")
    else:
        print("? Signal tracker not working as expected")
    
    # Test 5: Error notification
    print("\n" + "=" * 60)
    print("TEST 5: Error Alert")
    print("=" * 60)
    
    success = telegram.send_error_alert(
        error_message="This is a test error message",
        context="test_telegram_notifications.py"
    )
    
    if success:
        print("? Error alert sent - check your Telegram")
    else:
        print("? Failed to send error alert")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n? All tests completed! Check your Telegram for notifications.")
    print("\nIf you didn't receive messages:")
    print("  1. Verify bot token is correct in .env")
    print("  2. Verify chat ID is correct in .env")
    print("  3. Make sure you've started a chat with your bot")
    print("  4. Check bot permissions (must be able to send messages)")
    
    return True


def main():
    """Run async test"""
    try:
        asyncio.run(test_telegram())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n? Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

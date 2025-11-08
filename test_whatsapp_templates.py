#!/usr/bin/env python3
"""
Test WhatsApp Templates
Verifies template configuration and sends test messages
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.whatsapp_notifier import get_whatsapp_notifier

load_dotenv()


def load_template_config():
    """Load template configuration"""
    config_path = 'whatsapp_templates/template_config.json'
    
    if not os.path.exists(config_path):
        print("❌ Template configuration not found!")
        print(f"   Expected: {config_path}")
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)


def print_template_status(config):
    """Print status of all templates"""
    print("\n" + "="*70)
    print("  WhatsApp Template Status")
    print("="*70 + "\n")
    
    templates = config.get('templates', {})
    
    status_emoji = {
        'approved': '✅',
        'pending_approval': '⏳',
        'rejected': '❌',
        'draft': '📝'
    }
    
    print(f"{'Template':<30} {'Status':<20} {'Content SID':<15}")
    print("-" * 70)
    
    for template_name, template_data in templates.items():
        status = template_data.get('status', 'unknown')
        content_sid = template_data.get('content_sid', '')
        sid_display = content_sid[:12] + "..." if content_sid else "Not set"
        emoji = status_emoji.get(status, '❓')
        
        print(f"{template_name:<30} {emoji} {status:<18} {sid_display}")
    
    print("\n" + "-" * 70)
    approval_status = config.get('approval_status', {})
    print(f"\nTotal: {approval_status.get('total_templates', 0)} | "
          f"✅ Approved: {approval_status.get('approved', 0)} | "
          f"⏳ Pending: {approval_status.get('pending', 0)} | "
          f"❌ Rejected: {approval_status.get('rejected', 0)}")
    print()


def test_signal_change_alert(notifier):
    """Test signal change alert template"""
    print("\n📊 Testing Signal Change Alert...")
    
    try:
        result = notifier.send_signal_change_alert(
            coin='BTC',
            old_signal='HOLD',
            new_signal='BUY',
            price=75420.00,
            confidence=0.87,
            llm_signal={
                'signal': 'BUY',
                'confidence': 'HIGH',
                'confidence_score': 0.90,
                'reasoning': 'Strong bullish momentum with RSI recovery from oversold conditions. Volume surge confirms buyer interest at support level.',
                'stop_loss': 73200.00,
                'take_profit': 78500.00
            },
            deep_analysis={
                'signal': 'BUY',
                'confidence_score': 0.85,
                'summary': 'Technical indicators show bullish convergence with MACD golden cross and ascending triangle formation.'
            }
        )
        
        if result:
            print("   ✅ Signal change alert sent successfully")
        else:
            print("   ❌ Failed to send signal change alert")
        
        return result
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_trade_execution(notifier):
    """Test trade execution template"""
    print("\n💰 Testing Trade Execution Alert...")
    
    try:
        result = notifier.send_trade_execution_alert(
            coin='BTC',
            action='BUY',
            amount=0.0125,
            price=75420.00,
            total_value=942.75,
            balance_usdt=57.25,
            balance_coin=0.0125
        )
        
        if result:
            print("   ✅ Trade execution alert sent successfully")
        else:
            print("   ❌ Failed to send trade execution alert")
        
        return result
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_deep_market_analysis(notifier):
    """Test deep market analysis template"""
    print("\n🔍 Testing Deep Market Analysis...")
    
    try:
        analysis = {
            'trend': 'BULLISH',
            'recommended_action': 'BUY',
            'confidence': 0.85,
            'risk_level': 'MEDIUM',
            'reasoning': 'Strong accumulation phase with institutional buying detected. RSI recovering from oversold territory while maintaining bullish momentum. Volume profile shows significant support at $73K level. MACD showing positive divergence indicating potential trend reversal.',
            'key_indicators': {
                'rsi': 42.5,
                'adx': 28.3,
                'volatility_ratio': 0.015
            },
            'support_levels': [73200.00, 71500.00],
            'resistance_levels': [77800.00, 79500.00],
            'stop_loss_suggestion': 72500.00,
            'take_profit_suggestion': 78500.00,
            'key_patterns': ['Ascending Triangle', 'Golden Cross', 'Volume Breakout'],
            'sentiment_score': 0.62,
            'warnings': ['Watch resistance at $77.8K', 'High volatility expected near resistance'],
            'ai_model_used': 'Claude Sonnet 4.5',
            'macro_trend': 'Market showing optimistic sentiment with increasing institutional accumulation.'
        }
        
        result = notifier.send_deep_analysis_report(
            coin='BTC',
            price=75420.00,
            analysis=analysis
        )
        
        if result:
            print("   ✅ Deep market analysis sent successfully")
        else:
            print("   ❌ Failed to send deep market analysis")
        
        return result
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_bot_status(notifier):
    """Test bot status template"""
    print("\n🤖 Testing Bot Status Alert...")
    
    try:
        result = notifier.test_connection()
        
        if result:
            print("   ✅ Bot status alert sent successfully")
        else:
            print("   ❌ Failed to send bot status alert")
        
        return result
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_error_alert(notifier):
    """Test error alert template"""
    print("\n⚠️  Testing Error Alert...")
    
    try:
        result = notifier.send_error_alert(
            error_message="WebSocket connection lost. Attempting automatic reconnection.",
            context="Kraken WebSocket"
        )
        
        if result:
            print("   ✅ Error alert sent successfully")
        else:
            print("   ❌ Failed to send error alert")
        
        return result
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("  WhatsApp Template Testing Suite")
    print("="*70)
    
    # Load configuration
    config = load_template_config()
    if not config:
        return
    
    # Show template status
    print_template_status(config)
    
    # Initialize notifier
    notifier = get_whatsapp_notifier()
    
    if not notifier.enabled:
        print("❌ WhatsApp notifier is not enabled!")
        print("\nPlease configure the following in your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_WHATSAPP_FROM=whatsapp:+15558419388")
        print("  TWILIO_WHATSAPP_TO=whatsapp:+1234567890")
        return
    
    print("\n" + "="*70)
    print("  Running Template Tests")
    print("="*70)
    
    # Check if we're in template mode
    if notifier.use_templates:
        print("\n⚠️  Note: Running in TEMPLATE MODE")
        print("   Templates must be approved by WhatsApp to work")
        print("   If templates are not approved, messages will fail\n")
    else:
        print("\n✅ Running in FREEFORM MODE (Sandbox)")
        print("   Messages will be sent as freeform text\n")
    
    # Ask user which tests to run
    print("\nWhich tests would you like to run?")
    print("1. Signal Change Alert")
    print("2. Trade Execution Alert")
    print("3. Deep Market Analysis (COMPREHENSIVE)")
    print("4. Bot Status")
    print("5. Error Alert")
    print("6. All Tests")
    print("7. Exit")
    
    choice = input("\nSelect option (1-7): ").strip()
    
    results = {}
    
    if choice == '1':
        results['signal_change'] = test_signal_change_alert(notifier)
    elif choice == '2':
        results['trade_execution'] = test_trade_execution(notifier)
    elif choice == '3':
        results['deep_analysis'] = test_deep_market_analysis(notifier)
    elif choice == '4':
        results['bot_status'] = test_bot_status(notifier)
    elif choice == '5':
        results['error_alert'] = test_error_alert(notifier)
    elif choice == '6':
        results['signal_change'] = test_signal_change_alert(notifier)
        results['trade_execution'] = test_trade_execution(notifier)
        results['deep_analysis'] = test_deep_market_analysis(notifier)
        results['bot_status'] = test_bot_status(notifier)
        results['error_alert'] = test_error_alert(notifier)
    elif choice == '7':
        print("\n👋 Goodbye!\n")
        return
    else:
        print("❌ Invalid option")
        return
    
    # Summary
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70 + "\n")
    
    if results:
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name:<25} {status}")
        
        print(f"\n  Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n  🎉 All tests passed! Check your WhatsApp for messages.")
        else:
            print("\n  ⚠️  Some tests failed. Check logs for details:")
            print("     tail -f whatsapp_notifier.log")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()

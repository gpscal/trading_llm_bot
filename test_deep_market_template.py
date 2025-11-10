#!/usr/bin/env python3
"""
Test Deep Market Analysis WhatsApp Template
Non-interactive test specifically for the approved deep_market_analysis template
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from utils.whatsapp_notifier import get_whatsapp_notifier

load_dotenv()


def test_deep_market_analysis_template():
    """Test the deep market analysis template with comprehensive data"""
    
    print("\n" + "="*70)
    print("  Testing Deep Market Analysis WhatsApp Template")
    print("="*70 + "\n")
    
    # Initialize notifier
    notifier = get_whatsapp_notifier()
    
    if not notifier.enabled:
        print("❌ WhatsApp notifier is not enabled!")
        print("\nPlease configure the following in your .env file:")
        print("  TWILIO_ACCOUNT_SID=your_account_sid")
        print("  TWILIO_AUTH_TOKEN=your_auth_token")
        print("  TWILIO_WHATSAPP_FROM=whatsapp:+your_twilio_number")
        print("  TWILIO_WHATSAPP_TO=whatsapp:+your_phone_number")
        return False
    
    print(f"✅ WhatsApp notifier initialized")
    print(f"   From: {notifier.from_number}")
    print(f"   To: {notifier.to_number}")
    print(f"   Mode: {'Template' if notifier.use_templates else 'Freeform (Sandbox)'}\n")
    
    # Create comprehensive test data matching the template structure
    coin = "BTC"
    price = 75420.00
    
    analysis = {
        'trend': 'BULLISH',
        'recommended_action': 'BUY',
        'confidence': 0.85,
        'risk_level': 'MEDIUM',
        'reasoning': 'Strong accumulation phase with institutional buying detected. RSI recovering from oversold territory while maintaining bullish momentum. Volume profile shows significant support at $73K level. MACD showing positive divergence indicating potential trend reversal.',
        
        # Technical indicators
        'key_indicators': {
            'rsi': 42.5,
            'adx': 28.3,
            'volatility_ratio': 0.015,
            'macd': 'Bullish crossover detected',
            'volume': 'Above average'
        },
        
        # Price levels
        'support_levels': [73200.00, 71500.00],
        'resistance_levels': [77800.00, 79500.00],
        'stop_loss_suggestion': 72500.00,
        'take_profit_suggestion': 78500.00,
        
        # Patterns and warnings
        'key_patterns': [
            'Ascending triangle formation',
            'Golden cross on 4H chart',
            'Volume breakout pattern'
        ],
        'warnings': [
            'Watch for resistance at $77.8K',
            'High volatility expected near resistance'
        ],
        
        # Market sentiment
        'sentiment_score': 0.62,  # Fear & Greed Index
        'macro_trend': 'Market showing optimistic sentiment with increasing buy pressure. Institutional accumulation continues.',
        
        # News sentiment (enhanced data)
        'news_sentiment': {
            'label': 'BULLISH',
            'score': 0.68,
            'article_count': 10,
            'top_headlines': [
                {'title': 'Bitcoin surges past $75K amid institutional adoption wave'},
                {'title': 'Major exchange reports record trading volume in crypto markets'},
                {'title': 'Analysts predict continued upward momentum for digital assets'}
            ]
        },
        'news_summary': 'Analyzed 10 recent articles. Overall sentiment is positive with mentions of gains, adoption, and growth.',
        
        # AI model
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("📊 Test Data Summary:")
    print(f"   Coin: {coin}")
    print(f"   Price: ${price:,.2f}")
    print(f"   Action: {analysis['recommended_action']}")
    print(f"   Confidence: {analysis['confidence']:.0%}")
    print(f"   Trend: {analysis['trend']}")
    print(f"   Risk: {analysis['risk_level']}")
    print(f"   News Sentiment: {analysis['news_sentiment']['label']}")
    print(f"   News Articles: {analysis['news_sentiment']['article_count']}")
    print()
    
    # Send the deep analysis report
    print("📤 Sending deep market analysis...")
    
    try:
        result = notifier.send_deep_analysis_report(
            coin=coin,
            price=price,
            analysis=analysis
        )
        
        if result:
            print("✅ Deep market analysis sent successfully!\n")
            print("📱 Check your WhatsApp for the message.")
            print()
            
            if notifier.use_templates:
                print("✨ Message was sent using the approved WhatsApp template")
                print("   Template: deep_market_analysis")
                print("   Content SID: HXa150023aee81063cc8dc9cb944507283")
            else:
                print("ℹ️  Message was sent in freeform mode (Sandbox)")
                print("   To use templates, configure a production WhatsApp number")
            
            print()
            print("="*70)
            print("  Test Results")
            print("="*70)
            print()
            print("  ✅ Template test PASSED")
            print()
            print("  The deep market analysis template is working correctly!")
            print("  You should receive a comprehensive market analysis message")
            print("  with all technical indicators, news sentiment, and AI analysis.")
            print()
            
            return True
        else:
            print("❌ Failed to send deep market analysis\n")
            print("Check the logs for more details:")
            print("  tail -f whatsapp_notifier.log")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    try:
        success = test_deep_market_analysis_template()
        
        if success:
            print("="*70)
            print()
            sys.exit(0)
        else:
            print("="*70)
            print()
            print("⚠️  Test failed. Common issues:")
            print("  1. Check your Twilio credentials in .env")
            print("  2. Verify the WhatsApp sandbox is still active (if using sandbox)")
            print("  3. Ensure the template Content SID is correct")
            print("  4. Check whatsapp_notifier.log for detailed error messages")
            print()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user\n")
        sys.exit(130)


if __name__ == '__main__':
    main()

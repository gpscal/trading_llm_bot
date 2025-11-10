#!/usr/bin/env python3
"""
Test Deep Market Analysis WhatsApp Template in PRODUCTION MODE
Tests the approved template with Content SID on production WhatsApp number
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from utils.whatsapp_notifier import WhatsAppNotifier

load_dotenv()


def test_deep_market_analysis_production():
    """Test the deep market analysis template using production WhatsApp number"""
    
    print("\n" + "="*70)
    print("  Testing Deep Market Analysis - PRODUCTION TEMPLATE MODE")
    print("="*70 + "\n")
    
    # Initialize notifier with PRODUCTION settings (force template mode)
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_FROM')  # Production number
    to_number = os.getenv('TWILIO_WHATSAPP_TO')
    
    if not all([account_sid, auth_token, from_number, to_number]):
        print("❌ Missing Twilio credentials!")
        print("\nRequired environment variables:")
        print("  TWILIO_ACCOUNT_SID")
        print("  TWILIO_AUTH_TOKEN")
        print("  TWILIO_WHATSAPP_FROM (production number)")
        print("  TWILIO_WHATSAPP_TO")
        return False
    
    # Force template mode by explicitly setting use_templates=True
    notifier = WhatsAppNotifier(
        account_sid=account_sid,
        auth_token=auth_token,
        from_number=from_number,
        to_number=to_number,
        use_templates=True  # Force template mode
    )
    
    if not notifier.enabled:
        print("❌ WhatsApp notifier failed to initialize!")
        return False
    
    print(f"✅ WhatsApp notifier initialized")
    print(f"   From: {notifier.from_number}")
    print(f"   To: {notifier.to_number}")
    print(f"   Mode: {'✅ TEMPLATE MODE (Production)' if notifier.use_templates else '⚠️  Freeform'}")
    print()
    
    # Verify template configuration
    import json
    config_path = 'whatsapp_templates/template_config.json'
    
    if not os.path.exists(config_path):
        print(f"❌ Template configuration not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        template_config = json.load(f)
    
    deep_analysis_config = template_config.get('templates', {}).get('deep_market_analysis', {})
    content_sid = deep_analysis_config.get('content_sid', '')
    status = deep_analysis_config.get('status', '')
    
    print("📋 Template Configuration:")
    print(f"   Template: deep_market_analysis")
    print(f"   Content SID: {content_sid}")
    print(f"   Status: {status}")
    print(f"   Variables: {deep_analysis_config.get('variables_count', 0)}")
    print()
    
    if status != 'approved':
        print(f"⚠️  Warning: Template status is '{status}', expected 'approved'")
        print("   The template may not work until WhatsApp approves it.")
        print()
    
    if not content_sid:
        print("❌ Content SID is not configured!")
        print("   Please add the Content SID to template_config.json")
        return False
    
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
        'sentiment_score': 0.62,  # Fear & Greed Index (62% = Greed)
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
    print(f"   RSI: {analysis['key_indicators']['rsi']}")
    print(f"   ADX: {analysis['key_indicators']['adx']}")
    print(f"   News Sentiment: {analysis['news_sentiment']['label']}")
    print(f"   News Articles: {analysis['news_sentiment']['article_count']}")
    print(f"   Patterns: {len(analysis['key_patterns'])} detected")
    print(f"   Warnings: {len(analysis['warnings'])} active")
    print()
    
    # Send the deep analysis report
    print("📤 Sending deep market analysis using approved template...")
    print()
    
    try:
        result = notifier.send_deep_analysis_report(
            coin=coin,
            price=price,
            analysis=analysis
        )
        
        if result:
            print("✅ Deep market analysis sent successfully!\n")
            print("="*70)
            print("  🎉 SUCCESS - Template Test PASSED")
            print("="*70)
            print()
            print("📱 Check your WhatsApp for the comprehensive market analysis!")
            print()
            print("The message should include:")
            print("  ✓ Market recommendation (BUY) with 85% confidence")
            print("  ✓ Technical indicators (RSI, MACD, ADX, Volatility)")
            print("  ✓ Key price levels (Support, Resistance, Stop Loss, Take Profit)")
            print("  ✓ AI deep analysis reasoning")
            print("  ✓ Market sentiment (Fear & Greed Index)")
            print("  ✓ News analysis with sentiment and top headlines")
            print("  ✓ Key patterns and warnings")
            print()
            print("✨ Message was sent using the approved WhatsApp template:")
            print(f"   Template: deep_market_analysis")
            print(f"   Content SID: {content_sid}")
            print(f"   Variables: 31 parameters")
            print()
            
            return True
        else:
            print("❌ Failed to send deep market analysis\n")
            print("Possible reasons:")
            print("  1. Template not fully approved by WhatsApp yet")
            print("  2. Content SID is incorrect")
            print("  3. Template variables don't match the approved structure")
            print("  4. 24-hour messaging window expired (for production)")
            print()
            print("Check the logs for more details:")
            print("  tail -f whatsapp_notifier.log")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}\n")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """Main test function"""
    try:
        success = test_deep_market_analysis_production()
        
        print("="*70)
        print()
        
        if success:
            print("✅ Production template test completed successfully!")
            print()
            print("Next steps:")
            print("  • Verify the message format looks correct on WhatsApp")
            print("  • Check that all data fields are properly displayed")
            print("  • Confirm emojis and formatting render correctly")
            print("  • Test with different market conditions (SELL, HOLD signals)")
            print()
            sys.exit(0)
        else:
            print("⚠️  Test failed. Troubleshooting tips:")
            print()
            print("1. Verify template approval status in Twilio Console:")
            print("   https://console.twilio.com/us1/develop/sms/content-editor")
            print()
            print("2. Check that Content SID matches the approved template:")
            print("   Current: HXa150023aee81063cc8dc9cb944507283")
            print()
            print("3. Review logs for detailed error messages:")
            print("   tail -f whatsapp_notifier.log")
            print()
            print("4. If using production number, ensure 24-hour window is active:")
            print("   User must have messaged your bot within last 24 hours")
            print()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user\n")
        sys.exit(130)


if __name__ == '__main__':
    main()

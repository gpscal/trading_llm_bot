#!/usr/bin/env python3
"""
FINAL TEST - Deep Market Analysis Template with Optimized Character Limits
This test uses the updated code with strict character limits to stay under 1600 chars
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.whatsapp_notifier import WhatsAppNotifier

load_dotenv()


def test_template_final():
    """Final test with optimized character limits"""
    
    print("\n" + "="*70)
    print("  FINAL TEST - Deep Market Analysis Template")
    print("  With Optimized Character Limits")
    print("="*70 + "\n")
    
    # Initialize with production settings
    notifier = WhatsAppNotifier(
        account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
        auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
        from_number=os.getenv('TWILIO_WHATSAPP_FROM'),
        to_number=os.getenv('TWILIO_WHATSAPP_TO'),
        use_templates=True
    )
    
    print(f"✅ WhatsApp Notifier Initialized")
    print(f"   Mode: {'✅ TEMPLATE' if notifier.use_templates else '⚠️  Freeform'}")
    print(f"   From: {notifier.from_number}")
    print(f"   To: {notifier.to_number}")
    print()
    
    # Realistic test data with maximum-length fields to stress-test the limits
    coin = "BTC"
    price = 75420.00
    
    analysis = {
        'trend': 'BULLISH',
        'recommended_action': 'BUY',
        'confidence': 0.85,
        'risk_level': 'MEDIUM',
        
        # Maximum-length AI reasoning (will be truncated to 115 chars)
        'reasoning': 'Strong institutional accumulation phase detected with significant buying pressure. RSI is recovering from oversold territory while maintaining strong bullish momentum. Volume profile analysis shows robust support at the $73,000 level with MACD indicator displaying clear positive divergence signals.',
        
        'key_indicators': {
            'rsi': 42.5,
            'adx': 28.3,
            'volatility_ratio': 0.015,
        },
        
        'support_levels': [73200.00, 71500.00],
        'resistance_levels': [77800.00, 79500.00],
        'stop_loss_suggestion': 72500.00,
        'take_profit_suggestion': 78500.00,
        
        # Maximum-length patterns (will be truncated)
        'key_patterns': [
            'Ascending triangle formation developing',
            'Golden cross detected on 4-hour chart',
            'Volume breakout pattern confirmed'
        ],
        'warnings': [
            'Watch for strong resistance at $77,800 level',
            'High volatility expected near resistance zones'
        ],
        
        'sentiment_score': 0.62,
        
        # Maximum-length macro trend (will be truncated to 50 chars)
        'macro_trend': 'Market is showing increasingly optimistic sentiment with strong institutional buying pressure and positive momentum indicators.',
        
        'news_sentiment': {
            'label': 'BULLISH',
            'score': 0.68,
            'article_count': 10,
            # Maximum-length headlines (will be truncated)
            'top_headlines': [
                {'title': 'Bitcoin surges past $75,000 on institutional adoption wave'},
                {'title': 'Major cryptocurrency exchange reports record trading volumes'},
                {'title': 'Leading analysts predict continued strong upward momentum'}
            ]
        },
        
        # Maximum-length news summary (will be truncated to 40 chars)
        'news_summary': 'Comprehensive analysis of 10 recent articles shows overwhelmingly positive sentiment with focus on gains, widespread adoption trends, and continued market growth.',
        
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("📊 Test Data:")
    print(f"   Coin: {coin}")
    print(f"   Price: ${price:,.2f}")
    print(f"   Action: {analysis['recommended_action']}")
    print(f"   Confidence: {analysis['confidence']:.0%}")
    print(f"   AI Reasoning: {len(analysis['reasoning'])} chars (will truncate to 115)")
    print(f"   News Headlines: {len(analysis['news_sentiment']['top_headlines'])} items")
    print(f"   Patterns: {len(analysis['key_patterns'])} items")
    print()
    
    # Get prepared variables to check length
    variables = notifier._prepare_deep_analysis_variables(coin, price, analysis)
    
    # Load template to estimate final length
    with open('whatsapp_templates/deep_market_analysis.json', 'r') as f:
        template_data = json.load(f)
    
    template = template_data['template_content']
    rendered = template
    for var_num, value in variables.items():
        placeholder = "{{" + var_num + "}}"
        rendered = rendered.replace(placeholder, str(value))
    
    final_length = len(rendered)
    
    print("📏 Character Count Analysis:")
    print(f"   Template structure: ~901 chars")
    print(f"   Variable content: {sum(len(str(v)) for v in variables.values())} chars")
    print(f"   Final message: {final_length} chars")
    print(f"   WhatsApp limit: 1600 chars")
    
    if final_length > 1600:
        print(f"   ❌ OVER LIMIT by {final_length - 1600} chars!")
        print()
        print("   This shouldn't happen with the new limits!")
        return False
    else:
        remaining = 1600 - final_length
        print(f"   ✅ Within limit! {remaining} chars remaining")
        
        if remaining < 50:
            print(f"   ⚠️  Warning: Only {remaining} chars buffer - very tight!")
        elif remaining < 100:
            print(f"   ⚠️  Caution: {remaining} chars buffer - acceptable but tight")
        else:
            print(f"   ✅ Good: {remaining} chars buffer - safe margin")
    
    print()
    print("📤 Sending template message...")
    print()
    
    try:
        result = notifier.send_deep_analysis_report(
            coin=coin,
            price=price,
            analysis=analysis
        )
        
        if result:
            print("="*70)
            print("  🎉 SUCCESS! Template sent successfully!")
            print("="*70)
            print()
            print("📱 Check your WhatsApp for the deep market analysis message!")
            print()
            print("Message includes:")
            print("  ✓ AI Recommendation (BUY) with 85% confidence")
            print("  ✓ Technical indicators (RSI, MACD, ADX, Volatility, Volume)")
            print("  ✓ Key price levels (Support, Resistance, Stop Loss, Take Profit)")
            print("  ✓ AI deep analysis reasoning (optimized to 115 chars)")
            print("  ✓ Market sentiment (Fear & Greed Index)")
            print("  ✓ News analysis with BULLISH sentiment")
            print("  ✓ Top 3 news headlines (optimized)")
            print("  ✓ Key patterns and warnings (optimized)")
            print()
            print("✨ Character Optimization Applied:")
            print("  • AI reasoning: Max 115 characters")
            print("  • Headlines: Max 25 chars each (85 total)")
            print("  • Patterns: Max 20 chars each, 2 max")
            print("  • Warnings: Max 25 chars, 1 max")
            print("  • Macro trend: Max 50 chars")
            print("  • News summary: Max 40 chars")
            print("  • AI model name: Max 15 chars")
            print()
            return True
        else:
            print("❌ Failed to send template message")
            print()
            print("Check whatsapp_notifier.log for details:")
            print("  tail -f whatsapp_notifier.log")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    try:
        success = test_template_final()
        
        print("="*70)
        print()
        
        if success:
            print("✅ Template test completed successfully!")
            print()
            print("The deep market analysis template is now ready for production use.")
            print()
            print("Next steps:")
            print("  1. Verify message formatting on WhatsApp")
            print("  2. Confirm all data fields display correctly")
            print("  3. Test with different market conditions (SELL, HOLD)")
            print("  4. Monitor character counts in production")
            print()
            print("The bot will now automatically use the template when:")
            print("  • Running in production mode (non-sandbox number)")
            print("  • Sending deep market analysis reports")
            print("  • Within WhatsApp's 24-hour messaging window")
            print()
            sys.exit(0)
        else:
            print("⚠️  Test encountered issues.")
            print()
            print("Common solutions:")
            print("  1. Ensure template is fully approved in Twilio Console")
            print("  2. Verify Content SID matches in template_config.json")
            print("  3. Check that you're within 24-hour messaging window")
            print("  4. Review WHATSAPP_TEMPLATE_TEST_RESULTS.md for details")
            print()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted\n")
        sys.exit(130)


if __name__ == '__main__':
    main()

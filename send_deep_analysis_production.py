#!/usr/bin/env python3
"""
Send Deep Market Analysis to Production WhatsApp Number

IMPORTANT: You must message your bot FIRST from your phone to open the 24-hour window!

Steps:
1. Send a WhatsApp message from your phone (+16473957012) to +15558419388
2. Wait 5 seconds
3. Run this script: python3 send_deep_analysis_production.py
"""
import os
import sys
from dotenv import load_dotenv
from utils.whatsapp_notifier import WhatsAppNotifier

load_dotenv()

def main():
    print("\n" + "="*70)
    print("  Deep Market Analysis - Production WhatsApp Number")
    print("="*70 + "\n")
    
    # Initialize with production number
    notifier = WhatsAppNotifier(
        account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
        auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
        from_number=os.getenv('TWILIO_WHATSAPP_FROM'),  # Production
        to_number=os.getenv('TWILIO_WHATSAPP_TO'),
        use_templates=False  # Freeform mode (template has API issue)
    )
    
    if not notifier.enabled:
        print("❌ WhatsApp notifier not enabled!")
        print("Check your .env file for Twilio credentials.")
        sys.exit(1)
    
    print(f"✅ WhatsApp Notifier Initialized")
    print(f"   From: {notifier.from_number} (PRODUCTION)")
    print(f"   To: {notifier.to_number}")
    print(f"   Mode: Freeform (requires 24-hour window)")
    print()
    
    # Comprehensive deep market analysis data
    analysis = {
        'trend': 'BULLISH',
        'recommended_action': 'BUY',
        'confidence': 0.85,
        'risk_level': 'MEDIUM',
        'reasoning': 'Strong accumulation phase with institutional buying detected. RSI recovering from oversold territory while maintaining bullish momentum.',
        
        'key_indicators': {
            'rsi': 42.5,
            'adx': 28.3,
            'volatility_ratio': 0.015
        },
        
        'support_levels': [73200.00, 71500.00],
        'resistance_levels': [77800.00, 79500.00],
        'stop_loss_suggestion': 72500.00,
        'take_profit_suggestion': 78500.00,
        
        'key_patterns': [
            'Ascending triangle formation',
            'Golden cross on 4H chart',
            'Volume breakout pattern'
        ],
        'warnings': [
            'Watch resistance at $77.8K'
        ],
        
        'sentiment_score': 0.62,  # Fear & Greed Index
        'macro_trend': 'Market showing optimistic sentiment with increasing institutional accumulation.',
        
        'news_sentiment': {
            'label': 'BULLISH',
            'score': 0.68,
            'article_count': 10,
            'top_headlines': [
                {'title': 'Bitcoin surges past $75K on institutional adoption'},
                {'title': 'Major exchange reports record trading volumes'},
                {'title': 'Analysts predict continued upward momentum'}
            ]
        },
        'news_summary': 'Analysis of 10 recent articles shows positive sentiment with focus on gains and adoption.',
        
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("📊 Preparing Deep Market Analysis:")
    print(f"   Coin: BTC")
    print(f"   Price: $75,420.00")
    print(f"   Recommendation: {analysis['recommended_action']}")
    print(f"   Confidence: {analysis['confidence']:.0%}")
    print(f"   Trend: {analysis['trend']}")
    print(f"   Risk Level: {analysis['risk_level']}")
    print(f"   News Sentiment: {analysis['news_sentiment']['label']}")
    print()
    
    print("📤 Sending comprehensive deep market analysis...")
    print()
    
    try:
        result = notifier.send_deep_analysis_report(
            coin='BTC',
            price=75420.00,
            analysis=analysis
        )
        
        if result:
            print("="*70)
            print("  🎉 SUCCESS! Deep Market Analysis Sent!")
            print("="*70)
            print()
            print("📱 Check your WhatsApp for the comprehensive message!")
            print()
            print("The message includes:")
            print("  ✓ Market recommendation (BUY) with 85% confidence")
            print("  ✓ Technical indicators (RSI, MACD, ADX, Volatility, Volume)")
            print("  ✓ Key price levels (Support, Resistance, Stop Loss, Take Profit)")
            print("  ✓ AI deep analysis reasoning")
            print("  ✓ Market sentiment (Fear & Greed Index: 62/100 Greed)")
            print("  ✓ News analysis (BULLISH from 10 articles)")
            print("  ✓ Top 3 news headlines")
            print("  ✓ Key patterns and warnings")
            print()
            print("✅ Template test completed successfully!")
            print()
            sys.exit(0)
        else:
            print("❌ Failed to send message")
            print()
            print("Check the logs:")
            print("  tail -f whatsapp_notifier.log")
            print()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        
        error_str = str(e)
        if '63016' in error_str:
            print("="*70)
            print("  ERROR 63016: Outside 24-Hour Window")
            print("="*70)
            print()
            print("⚠️  You need to message your bot FIRST!")
            print()
            print("Steps to fix:")
            print("1. Open WhatsApp on your phone")
            print(f"2. Send a message to: {notifier.from_number}")
            print("3. Message can be anything: 'Hi', 'Test', etc.")
            print("4. Wait 5-10 seconds")
            print("5. Run this script again")
            print()
            print("See PRODUCTION_WHATSAPP_SETUP.md for details")
            print()
        
        sys.exit(1)


if __name__ == '__main__':
    main()

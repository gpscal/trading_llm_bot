#!/usr/bin/env python3
"""
Test Discord Deep Market Analysis Notification
SO MUCH EASIER THAN WHATSAPP! 🎉
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from utils.discord_notifier import get_discord_notifier

load_dotenv()


async def main():
    print("\n" + "="*70)
    print("  Testing Discord Deep Market Analysis")
    print("  (This is SO much easier than WhatsApp!)")
    print("="*70 + "\n")
    
    # Check Discord configuration
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    
    if not bot_token:
        print("❌ DISCORD_BOT_TOKEN not found in .env")
        print("   Please add: DISCORD_BOT_TOKEN=your_token")
        sys.exit(1)
    
    if not channel_id:
        print("❌ DISCORD_CHANNEL_ID not found in .env")
        print("   Please add: DISCORD_CHANNEL_ID=your_channel_id")
        sys.exit(1)
    
    print(f"✅ Discord Bot Token: {bot_token[:20]}...")
    print(f"✅ Discord Channel ID: {channel_id}")
    print()
    
    # Initialize Discord notifier
    print("📡 Connecting to Discord...")
    notifier = await get_discord_notifier()
    
    if not notifier.enabled:
        print("❌ Discord notifier not enabled!")
        sys.exit(1)
    
    print("✅ Connected to Discord!")
    print()
    
    # Prepare comprehensive test data
    coin = "BTC"
    price = 75420.00
    
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
        
        'key_patterns': [
            'Ascending triangle formation',
            'Golden cross on 4H chart',
            'Volume breakout pattern'
        ],
        'warnings': [
            'Watch for resistance at $77.8K',
            'High volatility expected near resistance zones'
        ],
        
        'sentiment_score': 0.62,
        'macro_trend': 'Market showing optimistic sentiment with increasing buy pressure. Institutional accumulation continues.',
        
        'news_sentiment': {
            'label': 'BULLISH',
            'score': 0.68,
            'article_count': 10,
            'top_headlines': [
                {'title': 'Bitcoin surges past $75K amid institutional adoption wave'},
                {'title': 'Major cryptocurrency exchange reports record trading volumes'},
                {'title': 'Leading analysts predict continued strong upward momentum'}
            ]
        },
        'news_summary': 'Analysis of 10 recent articles shows overwhelmingly positive sentiment.',
        
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("📊 Test Data:")
    print(f"   Coin: {coin}")
    print(f"   Price: ${price:,.2f}")
    print(f"   Action: {analysis['recommended_action']}")
    print(f"   Confidence: {analysis['confidence']:.0%}")
    print(f"   Trend: {analysis['trend']}")
    print(f"   News Sentiment: {analysis['news_sentiment']['label']}")
    print()
    
    print("📤 Sending deep market analysis to Discord...")
    print()
    
    try:
        result = await notifier.send_deep_analysis_report(
            coin=coin,
            price=price,
            analysis=analysis
        )
        
        if result:
            print("="*70)
            print("  🎉 SUCCESS! Message sent to Discord!")
            print("="*70)
            print()
            print("✅ Check your Discord channel for the deep market analysis!")
            print()
            print("The message includes:")
            print("  ✓ AI Recommendation (BUY) with 85% confidence")
            print("  ✓ Technical indicators (RSI, MACD, ADX, Volatility)")
            print("  ✓ Key price levels (Support, Resistance, Stop/Take Profit)")
            print("  ✓ AI deep analysis reasoning")
            print("  ✓ Market sentiment (Fear & Greed Index)")
            print("  ✓ News analysis with sentiment and headlines")
            print("  ✓ Key patterns and warnings")
            print()
            print("💚 Discord is SO much easier than WhatsApp!")
            print()
            
            # Clean shutdown
            await notifier.close()
            sys.exit(0)
        else:
            print("❌ Failed to send message")
            print()
            print("Check discord_notifier.log for details")
            await notifier.close()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        if notifier:
            await notifier.close()
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted\n")
        sys.exit(130)

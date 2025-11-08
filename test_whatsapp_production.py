#!/usr/bin/env python3
"""
Test WhatsApp Deep Analysis Notification with Production Number
Uses TWILIO_WHATSAPP_FROM and TWILIO_WHATSAPP_TO (ignores sandbox)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.whatsapp_notifier import WhatsAppNotifier


def test_production_whatsapp():
    """Test with production Twilio number"""
    
    print("\n" + "="*70)
    print("Testing WhatsApp Deep Analysis with PRODUCTION Number")
    print("="*70)
    
    # Get credentials from .env
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_FROM')  # Production number
    to_number = os.getenv('TWILIO_WHATSAPP_TO')
    
    # Validate credentials
    if not all([account_sid, auth_token, from_number, to_number]):
        print("❌ Missing production credentials in .env:")
        print(f"   TWILIO_ACCOUNT_SID: {'✓' if account_sid else '✗'}")
        print(f"   TWILIO_AUTH_TOKEN: {'✓' if auth_token else '✗'}")
        print(f"   TWILIO_WHATSAPP_FROM: {'✓' if from_number else '✗'}")
        print(f"   TWILIO_WHATSAPP_TO: {'✓' if to_number else '✗'}")
        return False
    
    print(f"\n✓ Production credentials found")
    print(f"  Account SID: {account_sid[:10]}...{account_sid[-4:]}")
    print(f"  From: {from_number}")
    print(f"  To: {to_number}")
    
    # Create WhatsApp notifier with production credentials (bypassing sandbox)
    # Force use_templates=False for testing (freeform messages)
    whatsapp = WhatsAppNotifier(
        account_sid=account_sid,
        auth_token=auth_token,
        from_number=from_number,
        to_number=to_number,
        use_templates=False  # Use freeform for testing
    )
    
    if not whatsapp.enabled:
        print("❌ Failed to initialize WhatsApp notifier")
        return False
    
    print(f"  Mode: Production (Freeform)")
    
    # Create mock deep analysis result with news sentiment
    mock_analysis = {
        'timestamp': datetime.now().isoformat(),
        'symbol': 'BTC/USD',
        'timeframe': 'multi',
        
        # Recommendation
        'trend': 'BULLISH',
        'recommended_action': 'BUY',
        'confidence': 0.78,
        
        # Technical indicators
        'support_levels': [48200.00, 47500.00, 46800.00],
        'resistance_levels': [51000.00, 52500.00, 54000.00],
        'key_indicators': {
            'rsi': 58.5,
            'macd': (120.5, 95.3),
            'adx': 32.7,
            'obv': 15000,
            'volatility_ratio': 0.018,
            'trend_strength': 0.65,
            'volume_profile': 'high'
        },
        'divergences': [],
        
        # Market context (Fear & Greed)
        'sentiment_score': 0.68,  # 68/100 = Greed
        
        # NEWS SENTIMENT (NEW!)
        'news_summary': 'Analyzed 10 recent articles. Overall sentiment is positive with mentions of gains, adoption, and growth.',
        'news_sentiment': {
            'score': 0.67,
            'label': 'BULLISH',
            'article_count': 10,
            'top_headlines': [
                {
                    'title': 'Bitcoin surges past $50,000 amid institutional adoption wave',
                    'source': 'CoinDesk',
                    'url': 'https://example.com/article1',
                    'date': '2025-11-08T12:00:00Z'
                },
                {
                    'title': 'Major banks announce crypto custody services expansion',
                    'source': 'Bloomberg',
                    'url': 'https://example.com/article2',
                    'date': '2025-11-08T11:30:00Z'
                },
                {
                    'title': 'Crypto ETF volumes hit record high as mainstream interest grows',
                    'source': 'Reuters',
                    'url': 'https://example.com/article3',
                    'date': '2025-11-08T10:45:00Z'
                }
            ]
        },
        
        'macro_trend': 'Strong uptrend with institutional accumulation',
        
        # Risk assessment
        'risk_level': 'MEDIUM',
        'stop_loss_suggestion': 47800.00,
        'take_profit_suggestion': 52500.00,
        
        # AI reasoning
        'reasoning': 'Strong technical setup with RSI in bullish zone and MACD showing positive momentum. '
                    'Volume profile indicates healthy accumulation. News sentiment strongly bullish with '
                    'institutional adoption narrative gaining traction. Support levels holding firm.',
        'key_patterns': [
            'Ascending triangle formation',
            'Golden cross on 4H chart',
            'Volume breakout confirmed'
        ],
        'warnings': [
            'Watch for resistance at $51K',
            'Profit taking possible near all-time high'
        ],
        
        # Metadata
        'analysis_duration': 12.5,
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("\n" + "="*70)
    print("Sending test notification with news sentiment...")
    print("="*70 + "\n")
    
    # Send notification
    result = whatsapp.send_deep_analysis_report(
        coin='BTC',
        price=50125.50,
        analysis=mock_analysis
    )
    
    if result:
        print("\n✅ SUCCESS! Deep analysis notification sent!")
        print("\n📱 Check your WhatsApp to see the notification.")
        print("\nExpected sections:")
        print("  ✓ AI Recommendation (🟢 BUY, 78% confidence)")
        print("  ✓ Technical Indicators (RSI, ADX, Volatility)")
        print("  ✓ Key Price Levels (Support, Resistance, Stops)")
        print("  ✓ AI Deep Analysis (Claude's reasoning)")
        print("  ✓ Market Sentiment (Fear & Greed: 68/100)")
        print("  ✓ 📰 NEWS ANALYSIS (NEW!)")
        print("    - Sentiment: BULLISH 📰🟢")
        print("    - Article count: 10")
        print("    - Top 3 headlines")
        print("  ✓ Key Patterns & Warnings")
        return True
    else:
        print("\n❌ FAILED to send notification")
        print("Check logs: whatsapp_notifier.log")
        return False


if __name__ == "__main__":
    try:
        success = test_production_whatsapp()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

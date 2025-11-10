#!/usr/bin/env python3
"""
Test deep market analysis with optimized variable lengths
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.whatsapp_notifier import WhatsAppNotifier

load_dotenv()

def test_optimized():
    """Test with shortened content to fit 1600 char limit"""
    
    print("\n" + "="*70)
    print("  Testing Deep Market Analysis - OPTIMIZED")
    print("="*70 + "\n")
    
    # Initialize with production settings
    notifier = WhatsAppNotifier(
        account_sid=os.getenv('TWILIO_ACCOUNT_SID'),
        auth_token=os.getenv('TWILIO_AUTH_TOKEN'),
        from_number=os.getenv('TWILIO_WHATSAPP_FROM'),
        to_number=os.getenv('TWILIO_WHATSAPP_TO'),
        use_templates=True
    )
    
    print(f"✅ Mode: {'Template' if notifier.use_templates else 'Freeform'}")
    print()
    
    # Optimized data - shorter strings to stay under 1600 chars
    coin = "BTC"
    price = 75420.00
    
    analysis = {
        'trend': 'BULLISH',
        'recommended_action': 'BUY',
        'confidence': 0.85,
        'risk_level': 'MEDIUM',
        # Shortened reasoning to ~220 chars instead of 400
        'reasoning': 'Strong accumulation with institutional buying. RSI recovering from oversold while maintaining bullish momentum. Volume shows support at $73K. MACD positive divergence.',
        
        'key_indicators': {
            'rsi': 42.5,
            'adx': 28.3,
            'volatility_ratio': 0.015,
        },
        
        'support_levels': [73200.00],
        'resistance_levels': [77800.00],
        'stop_loss_suggestion': 72500.00,
        'take_profit_suggestion': 78500.00,
        
        # Reduced to 2 patterns
        'key_patterns': [
            'Ascending triangle',
            'Golden cross on 4H'
        ],
        'warnings': [
            'Watch resistance at $77.8K'
        ],
        
        'sentiment_score': 0.62,
        # Shortened macro trend
        'macro_trend': 'Optimistic sentiment with buy pressure. Institutional accumulation continues.',
        
        'news_sentiment': {
            'label': 'BULLISH',
            'score': 0.68,
            'article_count': 10,
            # Shortened headlines (max 50 chars each)
            'top_headlines': [
                {'title': 'Bitcoin surges past $50K amid adoption'},
                {'title': 'Major exchange reports record volume'},
                {'title': 'Analysts predict upward momentum'}
            ]
        },
        # Shortened news summary
        'news_summary': 'Positive sentiment from 10 articles about gains and adoption.',
        
        'ai_model_used': 'Claude Sonnet 4.5'
    }
    
    print("📊 Sending optimized deep market analysis...")
    
    # Calculate approximate length
    import json
    with open('whatsapp_templates/deep_market_analysis.json', 'r') as f:
        template_data = json.load(f)
    
    # Prepare variables (matching the helper function)
    from utils.whatsapp_notifier import get_whatsapp_notifier
    test_notifier = get_whatsapp_notifier()
    variables = test_notifier._prepare_deep_analysis_variables(coin, price, analysis)
    
    # Estimate length
    template = template_data['template_content']
    rendered = template
    for var_num, value in variables.items():
        placeholder = "{{" + var_num + "}}"
        rendered = rendered.replace(placeholder, str(value))
    
    print(f"   Estimated length: {len(rendered)} chars (limit: 1600)")
    
    if len(rendered) > 1600:
        print(f"   ⚠️  Still {len(rendered) - 1600} chars over!")
    else:
        print(f"   ✅ Within limit! {1600 - len(rendered)} chars remaining")
    
    print()
    
    try:
        result = notifier.send_deep_analysis_report(
            coin=coin,
            price=price,
            analysis=analysis
        )
        
        if result:
            print("✅ Message sent successfully!")
            print()
            print("📱 Check your WhatsApp for the message")
            print()
            return True
        else:
            print("❌ Failed to send message")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_optimized()

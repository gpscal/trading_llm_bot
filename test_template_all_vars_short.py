#!/usr/bin/env python3
"""
Test with ALL 31 variables but using SHORT values to stay under 1600 chars
"""
import os
import json
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

content_sid = "HXa150023aee81063cc8dc9cb944507283"
from_number = os.getenv('TWILIO_WHATSAPP_FROM')
to_number = os.getenv('TWILIO_WHATSAPP_TO')

print("Testing with ALL 31 variables (SHORT values)")
print("="*70)
print()

# All 31 variables with VERY short values
variables = {
    "1": "BTC",                           # Coin
    "2": "75420",                         # Price (no commas to save chars)
    "3": "2025-11-10 12:00",             # Timestamp
    "4": "🟢",                            # Action emoji
    "5": "BUY",                           # Action
    "6": "85%",                           # Confidence
    "7": "📈",                            # Trend emoji
    "8": "BULLISH",                       # Trend
    "9": "🟡",                            # Risk emoji
    "10": "MEDIUM",                       # Risk level
    "11": "42.5",                         # RSI
    "12": "Neutral",                      # RSI status
    "13": "Bullish cross",                # MACD (shortened)
    "14": "28.3",                         # ADX
    "15": "Strong",                       # ADX status (shortened)
    "16": "Moderate",                     # Volatility
    "17": "Above avg",                    # Volume (shortened)
    "18": "73200",                        # Support (no commas)
    "19": "77800",                        # Resistance
    "20": "72500",                        # Stop loss
    "21": "78500",                        # Take profit
    "22": "Strong accumulation. RSI recovering with bullish momentum. Support at $73K. MACD positive divergence.",  # AI reasoning (~120 chars)
    "23": "Fear & Greed: 62/100 (Greed)",  # Sentiment
    "24": "Optimistic sentiment with buy pressure.",  # Macro trend (~45 chars)
    "25": "• Ascending triangle\n• Golden cross\n⚠️ Watch $77.8K",  # Patterns (~55 chars)
    "26": "Claude 4.5",                   # AI model (shortened)
    "27": "10 articles show positive sentiment.",  # News summary (~40 chars)
    "28": "📰🟢",                          # News emoji
    "29": "BULLISH",                      # News label
    "30": "10",                           # Article count
    "31": "• BTC surges on adoption\n• Record volume\n• Upward momentum"  # Headlines (~60 chars)
}

print("Variables:")
for k, v in variables.items():
    print(f"  {k}: {v[:50]}{'...' if len(v) > 50 else ''}")

print()

# Estimate total length
template_structure = 901  # Base template length
variable_content = sum(len(str(v)) for v in variables.values())
estimated_total = template_structure + variable_content

print(f"Template structure: ~901 chars")
print(f"Variable content: {variable_content} chars")
print(f"Estimated total: {estimated_total} chars")
print(f"WhatsApp limit: 1600 chars")

if estimated_total > 1600:
    print(f"❌ Still {estimated_total - 1600} chars OVER!")
else:
    print(f"✅ Within limit! {1600 - estimated_total} chars remaining")

print()
print("Attempting to send...")

try:
    msg = client.messages.create(
        from_=from_number,
        to=to_number,
        content_sid=content_sid,
        content_variables=json.dumps(variables)
    )
    print(f"✅ SUCCESS! Message SID: {msg.sid}")
    print()
    print("🎉 The template works! Check your WhatsApp!")
    print()
    print("Key findings:")
    print("  • All 31 variables must be provided")
    print("  • Total message must be under 1600 characters")
    print("  • Keep AI reasoning under 120 chars")
    print("  • Keep headlines under 60 chars total")
    print("  • Keep other text fields concise")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    print()
    if "1600" in str(e):
        print("Still exceeding 1600 char limit. Need to shorten further:")
        print("  • AI reasoning: Currently ~120, try ~100")
        print("  • Headlines: Currently ~60, try ~50")
        print("  • Patterns: Currently ~55, try ~40")

print()
print("="*70)

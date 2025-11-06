# WhatsApp Notifications - Quick Reference 📱

## Overview
Your trading bot sends two types of WhatsApp notifications:

## 1. Real-Time Signal Changes ⚡ (Fast LLM)
**Frequency**: Every ~60 seconds (when signal changes)  
**Source**: DeepSeek R1 LLM Advisor  
**Purpose**: Quick trading signals

### What You Get:
```
🔔 SIGNAL CHANGE ALERT
- Coin & Price
- Old Signal → New Signal
- Confidence level
- LLM reasoning (summarized)
- Stop loss / Take profit levels
```

### Example:
```
🔔 *SIGNAL CHANGE ALERT*
==============================
*Coin:* BTC
*Price:* $95,750.50

*Signal Change:*
⏸️ HOLD → 🟢 *BUY*
*Confidence:* 72.5%

*🤖 LLM Advisor:*
🟢 Signal: *BUY*
📊 Confidence: HIGH (72.5%)
📖 Analysis:
_Strong bullish momentum with RSI at 58..._

🛑 Stop Loss: $92,500.00
🎯 Take Profit: $98,000.00
```

---

## 2. Deep Market Analysis 🧠 (Claude Haiku)
**Frequency**: Every 2 hours  
**Source**: Claude Haiku 4.5 + Fear & Greed Index  
**Purpose**: Comprehensive market analysis

### What You Get:
```
🧠 DEEP MARKET ANALYSIS
- Comprehensive recommendation
- Technical indicators analysis
- Support/Resistance levels
- Risk assessment
- Chart patterns
- Market sentiment
- AI reasoning (detailed)
- Macro trend outlook
- Warning alerts
```

### Example:
```
🧠 *DEEP MARKET ANALYSIS*
==============================
*BTC/USD* @ $95,750.50

*📊 Recommendation:*
🟢 *BUY* (Confidence: 78%)
📈 Trend: *BULLISH*
⚠️ Risk: MEDIUM

*📉 Technical Indicators:*
RSI: 58.5 (Neutral)
ADX: 32.4 (Strong trend)
Volatility: Normal

*🎯 Key Levels:*
Support: $93,250.00
Resistance: $98,500.00

*💰 Trade Levels:*
🛑 Stop Loss: $92,500.00
🎯 Take Profit: $105,000.00

*🔍 Patterns:* strong_trend, higher_highs

*😨 Market Sentiment:*
Fear & Greed: 52/100 (Neutral)

*🧠 AI Analysis:*
_Strong bullish momentum detected..._

*⚠️ Warnings:*
• Watch for profit-taking near resistance
```

---

## Comparison

| Feature | Signal Change | Deep Analysis |
|---------|--------------|---------------|
| **Frequency** | ~60 seconds | 2 hours |
| **AI Model** | DeepSeek R1 | Claude Haiku 4.5 |
| **Response Time** | Fast | Comprehensive |
| **Data Sources** | Technical indicators | Indicators + Sentiment + News |
| **Best For** | Quick trades | Strategic planning |
| **Detail Level** | Summary | In-depth |

---

## How They Work Together

```
Real-time Loop (60s):
  ↓
  Fast LLM analyzes indicators
  ↓
  Signal change? → WhatsApp alert
  ↓
  Continue monitoring...

Every 2 Hours:
  ↓
  Deep Analyzer fetches comprehensive data
  ↓
  Claude Haiku analyzes market
  ↓
  WhatsApp deep analysis report
  ↓
  Cache for 2 hours, repeat
```

---

## Configuration

### Enable/Disable Notifications

**All notifications** (in `.env`):
```bash
# Keep credentials to enable
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=ab...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+16473957012

# Remove credentials to disable
```

### Change Deep Analysis Frequency

In `config/config.py`:
```python
'deep_analysis_interval': 7200,  # seconds

# Options:
# 3600 = 1 hour
# 7200 = 2 hours (default)
# 14400 = 4 hours
```

### Change Deep Analysis Model

In `.env`:
```bash
# Fast and cheap
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

# More powerful (but more expensive)
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

---

## Best Practices

### 📊 Using Signal Changes
- ✅ Act quickly on high-confidence signals
- ✅ Verify with technical chart
- ✅ Use provided stop loss levels
- ⚠️ Don't trade on every signal (wait for high confidence)

### 🧠 Using Deep Analysis
- ✅ Review comprehensive report
- ✅ Check warnings before trading
- ✅ Use for strategic planning
- ✅ Compare with signal changes
- ⚠️ Don't ignore risk assessments

### 🎯 Combining Both
1. **Deep Analysis**: Sets your strategic direction
2. **Signal Changes**: Provides tactical entry/exit points
3. **Agreement**: Strongest signals when both align
4. **Disagreement**: Wait for clarity or reduce position size

---

## Troubleshooting

### Not Receiving Messages?
1. ✅ Check Twilio credentials in `.env`
2. ✅ Verify WhatsApp sandbox approved (if using sandbox)
3. ✅ Check `whatsapp_notifier.log` for errors
4. ✅ Test connection: `python test_whatsapp_notifications.py`

### Too Many Messages?
- Increase `deep_analysis_interval` to 4 hours
- Signal changes only fire when signal actually changes

### Want Email Instead?
- Add Telegram notifier (similar setup)
- Or implement email notifier (similar to WhatsApp)

---

## Testing

### Test Signal Change Alert
```bash
python test_whatsapp_notifications.py
```

### Test Deep Analysis Report
```bash
python test_deep_analyzer.py
# Wait for analysis to complete
# Check WhatsApp for report
```

### Check WhatsApp Connection
```python
from utils.whatsapp_notifier import get_whatsapp_notifier
notifier = get_whatsapp_notifier()
notifier.test_connection()
```

---

## Logs

Monitor these files:
- `whatsapp_notifier.log` - WhatsApp send status
- `deep_analyzer.log` - Deep analysis generation
- `llm_advisor.log` - Fast LLM signals
- `trade_logic.log` - Trading decisions

---

## Summary

✅ **Fast Signals**: Real-time trading alerts  
✅ **Deep Analysis**: Comprehensive reports every 2 hours  
✅ **Mobile Access**: All notifications to WhatsApp  
✅ **Risk Management**: Stop loss and warnings included  
✅ **Cost Optimized**: Using efficient AI models  

**You're all set!** 🚀

Start your bot and check WhatsApp for notifications.

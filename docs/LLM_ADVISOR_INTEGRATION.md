# LLM Trading Advisor Integration Guide

## Overview

The LLM Trading Advisor integrates the [LLM_trader](https://github.com/gpscal/LLM_trader) library with the trading bot to provide AI-powered trading signals using Large Language Models. This advisor analyzes market conditions using advanced technical indicators and provides reasoned trading recommendations for **both SOL and BTC** trading.

## Architecture

The integration consists of:

1. **`ml/llm_advisor.py`** - Main adapter module that bridges the bot's data structures with LLM_trader
2. **Integration in `trade/trade_logic.py`** - LLM signals contribute to the overall confidence score
3. **Configuration in `config/config.py`** - Settings for enabling/disabling and weighting LLM signals

## Multi-Coin Support

The LLM advisor **fully supports both SOL and BTC trading**:

- **Coin-Aware Analysis**: The advisor automatically uses the correct coin's technical indicators based on your selected trading coin
- **Dynamic Symbol**: The LLM prompt includes the correct symbol (SOL/USD or BTC/USD)
- **Price-Accurate**: Uses the correct coin's price for all technical analysis
- **Context-Aware**: The LLM receives full market context for the coin you're trading

### How It Works

When you trade SOL:
```python
# LLM receives SOL indicators and analyzes SOL/USD
llm_signal = await llm_advisor.get_trading_signal(..., selected_coin='SOL')
# Result: Analysis based on SOL price, SOL RSI, SOL MACD, etc.
```

When you trade BTC:
```python
# LLM receives BTC indicators and analyzes BTC/USD
llm_signal = await llm_advisor.get_trading_signal(..., selected_coin='BTC')
# Result: Analysis based on BTC price, BTC RSI, BTC MACD, etc.
```

## How It Works

1. **Data Collection**: The advisor collects:
   - Current SOL and BTC prices (both coins monitored)
   - Technical indicators for the **selected trading coin** (RSI, MACD, ADX, OBV, Bollinger Bands, etc.)
   - Historical OHLCV data (if available)
   - Current balance (USDT and selected coin)

2. **LLM Analysis**: Sends a comprehensive prompt to the LLM model including:
   - Market data for the **selected trading coin** (SOL or BTC)
   - Technical analysis indicators for the selected coin
   - Market sentiment (optional)
   - Current position context
   - Symbol context (e.g., "SOL/USD" or "BTC/USD")

3. **Signal Extraction**: Parses LLM response to extract:
   - Trading signal (BUY/SELL/HOLD)
   - Confidence level (HIGH/MEDIUM/LOW)
   - Stop-loss and take-profit suggestions (optional)

4. **Confidence Boost**: The LLM signal modifies the bot's confidence score:
   - **Confirms indicators**: Positive boost (+)
   - **Contradicts indicators**: Negative boost (-)
   - **Suggests HOLD**: Neutral (no boost)

## Setup Instructions

### 1. Install Dependencies

The LLM advisor requires additional packages. Install them:

```bash
pip install ccxt tiktoken rich numba scipy openai
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Configure LLM Model

Create or edit `LLM_trader/config/model_config.ini`:

#### Option A: Using OpenRouter (Recommended for Testing)

[OpenRouter](https://openrouter.ai/) provides access to multiple LLM models through a unified API.

```ini
[model]
name = deepseek/deepseek-r1:free
base_url = https://openrouter.ai/api/v1
api_key = your_openrouter_api_key_here
```

**Free tier available**: DeepSeek R1 reasoning model has a free tier perfect for testing.

#### Option B: Using Local Model (LM Studio)

If you have a local LLM running (e.g., via LM Studio):

```ini
[model]
name = your_local_model_name
base_url = http://localhost:1234/v1
api_key = lm-studio
```

#### Option C: Using OpenAI API

```ini
[model]
name = gpt-4o-mini
base_url = https://api.openai.com/v1
api_key = your_openai_api_key_here
```

### 3. Enable LLM Advisor

Edit `config/config.py`:

```python
CONFIG = {
    # ... other settings ...
    
    # LLM Trading Advisor settings
    'llm_enabled': True,  # Enable LLM advisor
    'llm_confidence_weight': 0.25,  # How much LLM signal contributes (0.0-1.0)
    'llm_model_config_path': 'LLM_trader/config/model_config.ini',
}
```

### 4. Adjust Weighting

The `llm_confidence_weight` controls how much the LLM signal affects trading decisions:

- **0.1-0.2**: Light influence (advisory only)
- **0.25-0.35**: Moderate influence (balanced with other signals)
- **0.4-0.5**: Strong influence (LLM can override indicators)

Start with `0.25` and adjust based on performance.

## Rate Limiting & Caching

The LLM advisor implements smart caching to avoid excessive API calls:

- **Cache Duration**: 5 minutes (responses cached per price range)
- **Minimum Interval**: 60 seconds between API calls
- **Automatic Throttling**: Prevents API rate limit issues

This means the LLM is consulted approximately once per minute, not on every trade cycle.

## Integration with Existing Systems

The LLM advisor works **alongside** (not replaces) existing systems:

```
Total Confidence = 
    Indicator-based confidence +
    ML Prediction boost +
    Profitability Prediction boost +
    LLM Signal boost
```

### Example Decision Flow (Works for both SOL and BTC)

1. **Technical Indicators**: Calculate base confidence (e.g., 0.15)
2. **ML Prediction**: If ML agrees, add +0.10 boost ? 0.25
3. **Profitability Model**: If profitable, add +0.05 boost ? 0.30
4. **LLM Advisor**: If LLM confirms BUY on selected coin, add +0.20 boost ? **0.50**
5. **Final Decision**: 0.50 > threshold (0.01) ? **Execute trade**

## Monitoring & Debugging

### Log Messages

When LLM advisor is enabled, you'll see:

```
LLM Signal for SOL: BUY, Confidence: HIGH (0.80)
LLM [SOL]: BUY (HIGH, score: 0.80)
```

Or for BTC:

```
LLM Signal for BTC: SELL, Confidence: MEDIUM (0.50)
LLM [BTC]: SELL (MEDIUM, score: 0.50)
```

### Log File

LLM advisor logs to `llm_advisor.log`:

```bash
tail -f llm_advisor.log
```

### Common Issues

#### 1. "Failed to initialize LLM Advisor"

**Cause**: Missing dependencies or invalid config file

**Solution**:
- Verify `LLM_trader/config/model_config.ini` exists and is valid
- Check API key is correct
- Ensure all dependencies are installed

#### 2. "LLM call throttled"

**Cause**: Too many calls in short time

**Solution**: Normal behavior - LLM advisor enforces 60s minimum interval. Wait for next cycle.

#### 3. "LLM signal skipped: [error]"

**Cause**: API connection issue or async context problem

**Solution**:
- Check API key and network connectivity
- Verify model endpoint is accessible
- Check logs for specific error details

#### 4. LLM Always Returns HOLD

**Cause**: Model is too conservative or prompt not optimized

**Solution**:
- Try different model (e.g., DeepSeek R1 reasoning model)
- Adjust `llm_confidence_weight` to reduce reliance
- Review LLM_trader prompt template for optimization

## Performance Considerations

### API Costs

- **OpenRouter (DeepSeek R1 Free)**: Free tier available
- **OpenAI GPT-4o-mini**: ~$0.15 per 1M tokens
- **Local Models**: No API cost, requires local GPU

### Latency

- **LLM API calls**: 2-10 seconds typically
- **Cached responses**: <1ms
- **Impact on trading**: Minimal (calls are async and cached)

### Accuracy

LLM signals are most useful when:
- ? Confirming existing indicator signals
- ? Providing context for unusual market conditions
- ? Adding reasoning for complex situations

Less useful when:
- ? Market conditions are clear and indicators are strong
- ? Latency-sensitive trading (high-frequency)
- ? Very volatile markets where signals change rapidly

## Best Practices

1. **Start Conservative**: Begin with `llm_confidence_weight: 0.15-0.20`
2. **Monitor Performance**: Track trades with/without LLM signals
3. **Gradual Increase**: Increase weight only if performance improves
4. **Use Free Tier First**: Test with OpenRouter free tier before committing to paid APIs
5. **Combine Signals**: LLM works best when combined with technical indicators and ML

## Disabling LLM Advisor

To disable:

```python
CONFIG = {
    'llm_enabled': False,  # Disable LLM advisor
}
```

Or simply remove/comment out the LLM advisor code sections.

## Troubleshooting

### Verify Setup

```python
python -c "
from ml.llm_advisor import get_llm_advisor
from config.config import CONFIG
advisor = get_llm_advisor(CONFIG)
print(f'LLM Advisor enabled: {advisor.enabled}')
print(f'Initialized: {advisor._initialized}')
"
```

### Test LLM Call (Manual)

```python
import asyncio
from ml.llm_advisor import get_llm_advisor
from config.config import CONFIG

advisor = get_llm_advisor(CONFIG)

# Test signal
signal = asyncio.run(advisor.get_trading_signal(
    sol_price=184.0,
    btc_price=65000.0,
    btc_indicators={'rsi': 50, 'macd': [0, 0], 'momentum': 100},
    sol_indicators={'rsi': 50, 'macd': [0, 0]},
    balance_usdt=1000.0,
    balance_sol=0.0
))

print(signal)
```

## Next Steps

1. ? Install dependencies
2. ? Configure model API key
3. ? Enable in config
4. ? Start with low weight (0.15-0.20)
5. ? Monitor performance
6. ? Adjust weight based on results

## References

- [LLM_trader Repository](https://github.com/gpscal/LLM_trader)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)

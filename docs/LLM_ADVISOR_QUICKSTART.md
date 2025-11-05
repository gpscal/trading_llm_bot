# LLM Advisor Quick Start

## ? Integration Complete!

The LLM Trading Advisor has been successfully integrated into SolBot. Here's what was added:

### Files Created/Modified

1. **`ml/llm_advisor.py`** - Main LLM advisor module
2. **`trade/trade_logic.py`** - Integrated LLM signals into trading decisions
3. **`config/config.py`** - Added LLM configuration settings
4. **`requirements.txt`** - Added LLM dependencies
5. **`docs/LLM_ADVISOR_INTEGRATION.md`** - Full documentation

### Quick Setup (3 Steps)

#### 1. Install Dependencies

```bash
pip install ccxt tiktoken rich numba scipy openai
```

#### 2. Configure LLM API

Edit `LLM_trader/config/model_config.ini`:

```ini
[model]
name = deepseek/deepseek-r1:free
base_url = https://openrouter.ai/api/v1
api_key = your_openrouter_api_key_here
```

Get a free API key: https://openrouter.ai/

#### 3. Enable in Config

Edit `config/config.py`:

```python
CONFIG = {
    # ... existing settings ...
    'llm_enabled': True,  # Enable LLM advisor
    'llm_confidence_weight': 0.25,  # Start conservative
}
```

## How It Works

The LLM advisor:
- ? Analyzes market conditions using your existing indicators
- ? Provides BUY/SELL/HOLD signals with reasoning
- ? Boosts confidence when confirming indicators
- ? Reduces confidence when contradicting indicators
- ? Caches responses (1 call per minute max)
- ? Works alongside ML predictions and profitability models

## Testing

### Verify Setup

```bash
python -c "
from ml.llm_advisor import get_llm_advisor
from config.config import CONFIG
advisor = get_llm_advisor(CONFIG)
print(f'Enabled: {advisor.enabled}, Initialized: {advisor._initialized}')
"
```

### Run Simulation

Start the simulation and watch for LLM signals in logs:

```bash
tail -f trade_logic.log | grep LLM
```

You should see:
```
LLM Signal: BUY, Confidence: 0.80, Boost: +0.20
LLM: BUY (confidence: 0.80, boost: +0.20)
```

## Troubleshooting

### "Failed to initialize LLM Advisor"

- Check `LLM_trader/config/model_config.ini` exists
- Verify API key is correct
- Ensure dependencies are installed

### "LLM call throttled"

Normal behavior - enforced 60s minimum interval between calls.

### No LLM signals in logs

- Check `llm_enabled: True` in config
- Verify API key works (test with OpenRouter dashboard)
- Check `llm_advisor.log` for errors

## Performance Tuning

Start with **low weight** (`0.15-0.20`) and monitor:

- If LLM improves results ? gradually increase weight
- If LLM hurts results ? reduce weight or disable
- Track trades with/without LLM signals

## Cost Considerations

**Free Options:**
- OpenRouter DeepSeek R1: Free tier available
- Local models (LM Studio): No API cost

**Paid Options:**
- OpenAI GPT-4o-mini: ~$0.15 per 1M tokens (~100-200 calls)
- OpenRouter premium models: Varies

With caching (1 call/minute), costs are minimal even with paid APIs.

## Next Steps

1. ? Install dependencies
2. ? Get OpenRouter API key (free)
3. ? Configure `model_config.ini`
4. ? Enable in config
5. ? Run simulation and monitor
6. ? Adjust weight based on performance

## Full Documentation

See `docs/LLM_ADVISOR_INTEGRATION.md` for complete details.

# Enabling LLM Advisor - Steps

## Quick Steps

### 1. Edit Config

Edit `config/config.py` and change:
```python
'llm_enabled': False,  # Change this to True
```

To:
```python
'llm_enabled': True,  # Enable LLM advisor
```

Optionally adjust the weight:
```python
'llm_confidence_weight': 0.25,  # How much LLM affects decisions (0.0-1.0)
```

### 2. Restart Services

**Required**: Restart the simulation service:
```bash
sudo systemctl restart solbot-simulation
```

**Optional**: Restart web dashboard (only if you want it to see the config change):
```bash
sudo systemctl restart solbot
```

### 3. Verify It's Working

Check logs:
```bash
# Check LLM advisor logs
tail -f llm_advisor.log | grep "LLM"

# Or check trade logic logs
tail -f trade_logic.log | grep "LLM"
```

You should see:
```
LLM Signal: BUY/SELL/HOLD, Confidence: HIGH/MEDIUM/LOW
LLM: BUY (confidence: 0.80, boost: +0.20)
```

### 4. Monitor Performance

Watch for LLM signals in your trading:
- LLM will call every ~60 seconds (cached)
- Signals appear in logs
- Confidence is boosted/reduced based on LLM advice

## Why Restart is Needed

Python imports config at startup. Running processes have the old config values cached. Restarting loads the new config.

## Troubleshooting

If you don't see LLM signals after restart:

1. **Check if enabled**:
   ```bash
   python -c "from config.config import CONFIG; print('LLM enabled:', CONFIG.get('llm_enabled'))"
   ```

2. **Check Ollama is running**:
   ```bash
   ollama list
   ```

3. **Check LLM advisor logs**:
   ```bash
   tail -20 llm_advisor.log
   ```

4. **Verify initialization**:
   ```bash
   tail -f trade_logic.log | grep -E "LLM|Initialized"
   ```

## Quick Restart Command

```bash
sudo systemctl restart solbot-simulation
```

Then wait ~10 seconds and check logs to confirm it's running.

# Profitability Model Issue & Solution

## Problem Identified

The profitability prediction model is **blocking ALL trades** because:

1. **Model was trained on poor data**:
   - 22 trade pairs analyzed
   - **0% were profitable** (all trades lost money)
   - Model learned that "everything is unprofitable"

2. **Model predictions**:
   - Predicting **0.1% probability** for all trades
   - This gives a **-0.20 confidence penalty** (making total confidence negative)

3. **Trade blocking**:
   - `min_profitability_threshold = 0.3` blocks trades when probability < 30%
   - Since model predicts 0.1%, ALL trades are blocked
   - Even if threshold passed, confidence penalty makes total confidence negative

## What You're Seeing

From logs:
```
Profitability Prediction - Prob: 0.001 (0.1%), Profitable: False, Boost: -0.199
Total Confidence: -0.10  (below 0.01 threshold)
Confidence too low. Skipping trade.
```

**Result**: No trades execute for hours/days

## Solution Applied

1. **Disabled profitability prediction** (for now):
   - Set `profitability_prediction_enabled: False`
   - Trades will execute based on indicators only

2. **Reduced threshold** (for when re-enabled):
   - `min_profitability_threshold: 0.0` (was 0.3)
   - Won't block trades based on profitability alone

3. **Reduced weight** (for when re-enabled):
   - `profitability_boost_weight: 0.2` (was 0.4)
   - Less influence on confidence score

## Next Steps

### Option 1: Run Without Profitability Prediction (Recommended Now)
- Already done in config
- Bot will trade based on technical indicators
- Trades should execute normally

### Option 2: Retrain Model with Better Data
After accumulating more trades (50-100+):
```bash
python ml/train_from_outcomes.py
```

Make sure you have:
- More trade pairs (50+)
- Some profitable trades (aim for >30% profitable)
- Diverse market conditions

### Option 3: Temporarily Re-enable with Lower Threshold
If you want to use it anyway:
```python
'profitability_prediction_enabled': True,
'min_profitability_threshold': 0.0,  # Don't block trades
'profitability_boost_weight': 0.1,   # Very minimal influence
```

## Why This Happened

The model learned from bad data:
- Your trading strategy in that period was unprofitable
- Model correctly learned "these conditions = unprofitable"
- But it's too conservative and blocks everything

## Recommendation

1. **Disable it for now** (already done)
2. **Run simulations** to generate more trades
3. **Wait until you have 50+ trades with better profitability** (>20% profitable)
4. **Retrain the model** with better data
5. **Re-enable with careful thresholds**

The model will get better as you accumulate more diverse trading data!

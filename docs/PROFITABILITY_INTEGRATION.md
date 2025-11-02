# Profitability Prediction Integration

## Overview

The profitability prediction model has been successfully integrated into the trading bot. This model learns from your actual trade outcomes (profitable vs unprofitable trades) and helps filter trades before execution.

## What Was Integrated

### 1. **Profitability Predictor Manager** (`ml/profitability_predictor_manager.py`)
   - Loads the trained profitability model
   - Makes real-time predictions on whether a trade will be profitable
   - Handles normalization and feature extraction
   - Returns probability scores (0-1) for trade profitability

### 2. **Trade Logic Integration** (`trade/trade_logic.py`)
   - Added profitability prediction checks before trade execution
   - Boosts confidence if model predicts profitable trade
   - Reduces confidence if model predicts unprofitable trade
   - Filters out trades with very low profitability probability (<30% by default)

### 3. **Configuration** (`config/config.py`)
   - Added profitability prediction settings:
     - `profitability_prediction_enabled`: Enable/disable (default: True)
     - `profitability_model_path`: Model file path
     - `profitability_norm_path`: Normalization parameters path
     - `profitability_boost_weight`: How much prediction affects confidence (0.4)
     - `min_profitability_threshold`: Minimum probability to trade (0.3)

### 4. **Historical Data Storage** (`utils/data_fetchers.py`)
   - Modified to store historical OHLCV data in balance object
   - Keeps last 100 candles for both SOL and BTC
   - Required for profitability prediction feature extraction

## How It Works

1. **During Trading Loop**:
   - Historical data is fetched and stored in `balance['sol_historical']` and `balance['btc_historical']`
   - When a trade is considered, profitability predictor extracts features from historical data
   - Model predicts probability (0-1) that trade will be profitable

2. **Confidence Boost**:
   - If probability > 0.5 (profitable): Adds positive boost to confidence
   - If probability < 0.5 (unprofitable): Subtracts from confidence
   - Boost amount = `(probability - 0.5) * profitability_boost_weight`

3. **Trade Filtering**:
   - If profitability probability < `min_profitability_threshold` (default 0.3), trade is skipped
   - This prevents executing trades that the model strongly predicts will lose money

## Usage

### Enable/Disable

In `config/config.py`:
```python
'profitability_prediction_enabled': True,  # Set to False to disable
```

### Adjust Settings

```python
# How much profitability prediction affects confidence
'profitability_boost_weight': 0.4,  # Range: 0.0-1.0 (higher = more influence)

# Minimum profitability probability to execute trade
'min_profitability_threshold': 0.3,  # Range: 0.0-1.0 (0.3 = 30% minimum)
```

### Retrain Model

After accumulating more trades:
```bash
python ml/train_from_outcomes.py
```

This will:
- Load new trades from `trade_log.json`
- Retrain the model with new data
- Save updated model to `models/profitability_predictor.pth`

## Log Messages

When profitability prediction is active, you'll see:
```
INFO: Profitability Prediction - Prob: 0.652, Profitable: True, Boost: 0.061
Profitability: 65.2% (boost: +0.06)
```

Or if prediction is low:
```
INFO: Profitability prediction too low (0.25). Skipping trade.
```

## Testing

### Manual Test
```python
from ml.profitability_predictor_manager import get_profitability_predictor_manager
from api.kraken import get_historical_data
import asyncio

async def test():
    manager = get_profitability_predictor_manager()
    manager.load_model()
    
    sol_historical = await get_historical_data('SOLUSDT', 60)
    btc_historical = await get_historical_data('XXBTZUSD', 60)
    
    prediction = manager.predict_profitability(sol_historical, btc_historical)
    print(f"Profitability: {prediction['probability']:.1%}")
    print(f"Profitable: {prediction['profitable']}")

asyncio.run(test())
```

## Integration Status

? **Model Training**: Complete - Model trained from 22 trade pairs  
? **Predictor Manager**: Complete - Loads and runs predictions  
? **Trade Logic Integration**: Complete - Predictions used in trade decisions  
? **Config Settings**: Complete - All settings configurable  
? **Historical Data**: Complete - Stored in balance object  
? **Logging**: Complete - Logs predictions and decisions  

## Next Steps

1. **Monitor Performance**: Run simulations and observe how profitability predictions affect trade quality
2. **Tune Thresholds**: Adjust `min_profitability_threshold` based on results
3. **Retrain Periodically**: Run `python ml/train_from_outcomes.py` after accumulating more trades
4. **Compare Strategies**: Test with profitability prediction enabled vs disabled to measure impact

## Troubleshooting

### "Model not found"
- Ensure model exists: `ls models/profitability_predictor.pth`
- If missing, train it: `python ml/train_from_outcomes.py`

### "Insufficient historical data"
- Check that `fetch_and_analyze_historical_data` is being called
- Verify balance contains `sol_historical` and `btc_historical`
- Need at least 60 candles for predictions

### "Feature size mismatch"
- Model was trained with 11 features, current data has 20
- Predictor manager handles this automatically (padding/truncation)
- If issues persist, retrain model with current feature set

### Prediction always same value
- Model may have overfitted (100% accuracy suggests this)
- Retrain with more diverse trade data
- Check that trade outcomes vary (both profitable and unprofitable trades needed)

## Files Modified

- `ml/profitability_predictor_manager.py` - NEW: Manager class
- `trade/trade_logic.py` - MODIFIED: Added profitability prediction integration
- `config/config.py` - MODIFIED: Added profitability settings
- `utils/data_fetchers.py` - MODIFIED: Store historical data in balance

## See Also

- `docs/TRAIN_FROM_OUTCOMES_GUIDE.md` - Training guide
- `ml/train_from_outcomes.py` - Training script
- `scripts/analyze_trade_outcomes.py` - Analysis script

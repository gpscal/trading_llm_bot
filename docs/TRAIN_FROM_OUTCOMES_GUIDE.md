# Training ML Model from Trade Outcomes

## Overview

The `ml/train_from_outcomes.py` script implements a complete training pipeline that learns from your actual trading results (profitable vs unprofitable trades) rather than just market patterns.

## What It Does

1. **Loads Trade History**: Reads `trade_log.json` and matches buy/sell pairs
2. **Calculates Outcomes**: Determines which trades were profitable (>0.5% after fees)
3. **Fetches Historical Data**: Gets OHLCV data covering all trade timestamps
4. **Extracts Features**: Creates feature sequences (60 candles) for each trade
5. **Trains Binary Classifier**: Trains an LSTM model to predict if a trade will be profitable
6. **Saves Model**: Saves the trained model and normalization parameters

## Usage

### Basic Usage

```bash
python ml/train_from_outcomes.py
```

### Requirements

- At least **10 trades** in `trade_log.json`
- Internet connection to fetch historical market data
- PyTorch installed (CPU or CUDA)

### What Gets Trained

The model learns:
- **Input**: 60 timesteps of market features (price, volume, RSI, MACD, etc.)
- **Output**: Probability that the trade will be profitable (0-1)

## Model Architecture

- **Type**: LSTM with Attention mechanism
- **Input**: (batch, 60, ~20 features)
- **Output**: Binary probability (profitable or not)
- **Loss**: Binary Cross-Entropy
- **Optimizer**: Adam with learning rate scheduling

## Output Files

After training, you'll get:

1. **`models/profitability_predictor_best.pth`** - Best model weights (during training)
2. **`models/profitability_predictor_[timestamp].pth`** - Final trained model
3. **`models/profitability_predictor.pth`** - Default model path
4. **`models/profitability_predictor_norm.json`** - Normalization parameters

## Integration with Trading

To use the trained model in your trading bot:

```python
from ml.train_from_outcomes import ProfitabilityPredictor
import torch
import numpy as np
import json

# Load model
model = ProfitabilityPredictor(input_size=20, hidden_size=64, num_layers=2)
model.load_state_dict(torch.load('models/profitability_predictor.pth'))
model.eval()

# Load normalization parameters
with open('models/profitability_predictor_norm.json', 'r') as f:
    norm_params = json.load(f)
    feature_mean = np.array(norm_params['mean'])
    feature_std = np.array(norm_params['std'])

# Extract features (from ml.feature_extractor or ml.data_collector)
features = extract_features(sol_ohlc, btc_ohlc)  # Shape: (60, 20)
features_seq = features[-60:].reshape(1, 60, 20)  # Add batch dimension

# Normalize
features_seq = (features_seq - feature_mean) / feature_std

# Predict
with torch.no_grad():
    features_tensor = torch.FloatTensor(features_seq)
    probability = model(features_tensor).item()

# Use probability in trading decision
if probability > 0.6:  # 60% confidence it will be profitable
    # Execute trade
    pass
```

## Training Details

### Hyperparameters

- **Epochs**: 50 (with early stopping)
- **Batch Size**: 16
- **Learning Rate**: 0.001 (with ReduceLROnPlateau scheduler)
- **Early Stopping**: Patience of 10 epochs
- **Dropout**: 0.2

### Data Split

- **Train**: 80%
- **Validation**: 20%
- **Shuffle**: Yes (random permutation)

### Feature Normalization

Features are normalized using mean and std from training data only (prevents data leakage).

## Troubleshooting

### "Not enough trades for training"
- Run more simulations: `python simulate.py`
- Need at least 10 matched buy/sell pairs

### "Could not fetch sufficient historical data"
- Check internet connection
- Kraken API might be rate limiting (wait and retry)
- Ensure trades are recent enough (within API's history window)

### "No valid training data extracted"
- Trade timestamps might be too old for available historical data
- Check that `trade_log.json` contains recent trades
- Try running simulations to generate fresh trade data

### Low Accuracy
- Model needs more training data (aim for 50+ trades)
- Class imbalance (too few profitable trades) can hurt performance
- Consider adjusting the profitability threshold (>0.5%)

## Future Improvements

1. **Incremental Learning**: Retrain periodically as new trades come in
2. **Feature Engineering**: Add more sophisticated features
3. **Ensemble Models**: Combine multiple models for better predictions
4. **Multi-class Classification**: Predict profit ranges (small/medium/large profit)
5. **Risk-Aware Predictions**: Incorporate risk metrics into training

## Example Output

```
INFO:__main__:Loading trade history...
INFO:__main__:Loaded 22 trades with outcomes
INFO:__main__:Profitable: 5, Unprofitable: 17 (22.7% profitable)
INFO:__main__:Fetching historical market data...
INFO:__main__:Fetched 720 SOL candles
INFO:__main__:Fetched 720 BTC candles
INFO:__main__:Creating training dataset...
INFO:__main__:Extracting features for 22 trades...
INFO:__main__:Processed 22/22 trades, 18 successful
INFO:__main__:Created training dataset: (18, 60, 20), labels: (18,)
INFO:__main__:Class distribution - Profitable: 4, Unprofitable: 14
INFO:__main__:Train: 14, Val: 4
INFO:__main__:Training on cpu with 14 samples...
INFO:__main__:Epoch 1/50 - Train Loss: 0.6234, Train Acc: 0.6429, Val Loss: 0.5891, Val Acc: 0.7500
...
INFO:__main__:Training complete!
INFO:__main__:Best validation loss: 0.5234
INFO:__main__:Model saved to models/profitability_predictor_20251102_123456.pth
```

## See Also

- `ml/trade_learner.py` - Trade outcome analysis
- `scripts/analyze_trade_outcomes.py` - Quick analysis script
- `ml/train_model.py` - Price prediction training (different approach)
- `docs/LEARNING_FROM_OUTCOMES.md` - Original learning concept

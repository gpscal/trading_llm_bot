"""
Real-time feature extraction for ML model inference.
Extracts features from current market data for live predictions.
"""

import sys
import os
# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import numpy as np
from typing import Dict, List, Optional
from strategies.indicators import calculate_indicators
import asyncio
# Note: get_historical_data is not needed here - historical data is passed in


class MLFeatureExtractor:
    """Extract features in real-time for ML inference."""
    
    def __init__(self):
        self.feature_history = []  # Cache recent features
        self.max_history = 100
    
    async def extract_features_for_prediction(self, 
                                             sol_historical: List,
                                             btc_historical: Optional[List] = None,
                                             balance: Optional[Dict] = None) -> Optional[np.ndarray]:
        """
        Extract features from current market state for ML prediction.
        
        Args:
            sol_historical: Recent SOL OHLCV candles (at least 60)
            btc_historical: Recent BTC OHLCV candles (optional)
            balance: Current balance dict with indicators (optional, used as fallback)
            
        Returns:
            Feature matrix of shape (sequence_length, num_features)
            Returns None if insufficient data
        """
        if len(sol_historical) < 60:
            return None
        
        # Get or calculate indicators
        if balance and 'sol_indicators' in balance:
            sol_indicators = balance['sol_indicators']
            btc_indicators = balance.get('btc_indicators', {})
        else:
            if btc_historical is None:
                btc_historical = sol_historical  # Fallback
            btc_indicators, sol_indicators = calculate_indicators(
                btc_historical or sol_historical,
                sol_historical
            )
        
        # Extract price arrays
        closes = np.array([float(c[4]) for c in sol_historical])
        opens = np.array([float(c[1]) for c in sol_historical])
        highs = np.array([float(c[2]) for c in sol_historical])
        lows = np.array([float(c[3]) for c in sol_historical])
        volumes = np.array([float(c[5]) if len(c) > 5 else 1000.0 for c in sol_historical])
        
        features = []
        
        # Price features (same as training)
        returns = np.diff(closes) / closes[:-1]
        returns = np.concatenate([[0], returns])
        
        # Volatility
        import pandas as pd
        volatility = pd.Series(returns).rolling(window=14, min_periods=1).std().values
        
        # Price ratios
        hl_ratio = (highs - lows) / closes
        co_ratio = (closes - opens) / (opens + 1e-8)
        
        # Normalized prices
        price_normalized = closes / (pd.Series(closes).rolling(window=20, min_periods=1).mean().values + 1e-8)
        
        features.append(returns)
        features.append(volatility)
        features.append(hl_ratio)
        features.append(co_ratio)
        features.append(price_normalized)
        
        # Technical indicators
        rsi = sol_indicators.get('rsi', 50.0)
        rsi_array = np.full(len(closes), (rsi / 100.0) if isinstance(rsi, (int, float)) else 0.5)
        features.append(rsi_array)
        
        macd_line = sol_indicators.get('macd', [0, 0])[0] if isinstance(sol_indicators.get('macd'), tuple) else 0
        macd_normalized = np.full(len(closes), macd_line / (closes[-1] + 1e-8) if closes[-1] > 0 else 0)
        features.append(macd_normalized)
        
        bb = sol_indicators.get('bollinger_bands', (0, 0, 0))
        if isinstance(bb, tuple) and len(bb) == 3:
            upper, middle, lower = bb
            if upper > lower:
                bb_position = (closes - lower) / (upper - lower + 1e-8)
                bb_position = np.clip(bb_position, 0, 1)
            else:
                bb_position = np.full(len(closes), 0.5)
        else:
            bb_position = np.full(len(closes), 0.5)
        features.append(bb_position)
        
        ma = sol_indicators.get('moving_avg', closes[-1])
        ma_ratio = closes / (ma + 1e-8) if ma > 0 else np.ones(len(closes))
        features.append(ma_ratio)
        
        atr = sol_indicators.get('atr', 0)
        if isinstance(atr, np.ndarray):
            atr_value = np.mean(atr) if len(atr) > 0 else 0
        else:
            atr_value = atr if isinstance(atr, (int, float)) else 0
        atr_normalized = np.full(len(closes), atr_value / (closes[-1] + 1e-8) if closes[-1] > 0 else 0)
        features.append(atr_normalized)
        
        # Volume features
        volume_ma = pd.Series(volumes).rolling(window=20, min_periods=1).mean().values
        volume_ratio = volumes / (volume_ma + 1e-8)
        features.append(volume_ratio)
        
        # Stack features
        feature_matrix = np.stack(features, axis=1)
        
        # Return last 60 timesteps (sequence_length)
        if len(feature_matrix) >= 60:
            return feature_matrix[-60:]
        return None
    
    def get_latest_features(self, balance: Dict) -> Optional[np.ndarray]:
        """Get latest features from cached history or balance."""
        # This is a simplified version - in production, maintain feature history
        # For now, return None to trigger async extraction
        return None

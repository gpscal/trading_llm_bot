"""
Data collection and preprocessing for ML model training.
Collects historical OHLCV data and calculates features.
"""

import sys
import os
# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from api.kraken import get_historical_data
from strategies.indicators import calculate_indicators
from config.config import CONFIG
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('ml_data_collector')


def extract_features(ohlc_data: List, btc_ohlc: Optional[List] = None) -> np.ndarray:
    """
    Extract features from OHLCV data for ML model.
    
    Features include:
    - Price features: OHLC, returns, volatility
    - Technical indicators: RSI, MACD, Bollinger Bands, etc.
    - Volume features: volume, volume MA
    - Cross-asset features: BTC correlation if available
    
    Returns:
        Feature matrix of shape (sequence_length, num_features)
    """
    if len(ohlc_data) < 60:
        return None
    
    # Convert to arrays
    closes = np.array([float(c[4]) for c in ohlc_data])
    opens = np.array([float(c[1]) for c in ohlc_data])
    highs = np.array([float(c[2]) for c in ohlc_data])
    lows = np.array([float(c[3]) for c in ohlc_data])
    volumes = np.array([float(c[5]) if len(c) > 5 else 1000.0 for c in ohlc_data])
    
    features = []
    
    # Price features
    returns = np.diff(closes) / closes[:-1]
    returns = np.concatenate([[0], returns])  # Pad first element
    
    # Volatility (rolling std of returns)
    volatility = pd.Series(returns).rolling(window=14, min_periods=1).std().values
    
    # Price ratios
    hl_ratio = (highs - lows) / closes
    co_ratio = (closes - opens) / opens
    
    # Normalized prices (relative to recent mean)
    price_normalized = closes / pd.Series(closes).rolling(window=20, min_periods=1).mean().values
    
    # Add price features
    features.append(returns)
    features.append(volatility)
    features.append(hl_ratio)
    features.append(co_ratio)
    features.append(price_normalized)
    
    # Technical indicators
    btc_indicators, sol_indicators = calculate_indicators(
        btc_ohlc or ohlc_data,  # Use BTC if available, else use SOL
        ohlc_data
    )
    
    # RSI (scaled to 0-1)
    rsi = sol_indicators.get('rsi', 50.0)
    if isinstance(rsi, (int, float)):
        rsi_array = np.full(len(closes), rsi / 100.0)
    else:
        rsi_array = np.full(len(closes), 0.5)
    features.append(rsi_array)
    
    # MACD
    macd_line = sol_indicators.get('macd', [0, 0])[0] if isinstance(sol_indicators.get('macd'), tuple) else 0
    macd_array = np.full(len(closes), macd_line / closes[-1] if closes[-1] > 0 else 0)
    features.append(macd_array)
    
    # Bollinger Bands position (0-1 scale)
    bb = sol_indicators.get('bollinger_bands', (0, 0, 0))
    if isinstance(bb, tuple) and len(bb) == 3:
        upper, middle, lower = bb
        if upper > lower:
            bb_position = (closes - lower) / (upper - lower)
            bb_position = np.clip(bb_position, 0, 1)
        else:
            bb_position = np.full(len(closes), 0.5)
    else:
        bb_position = np.full(len(closes), 0.5)
    features.append(bb_position)
    
    # Moving average position
    ma = sol_indicators.get('moving_avg', closes[-1])
    ma_ratio = closes / ma if ma > 0 else np.ones(len(closes))
    features.append(ma_ratio)
    
    # ATR (normalized)
    atr = sol_indicators.get('atr', 0)
    if isinstance(atr, np.ndarray):
        atr_value = np.mean(atr) if len(atr) > 0 else 0
    else:
        atr_value = atr if isinstance(atr, (int, float)) else 0
    atr_normalized = np.full(len(closes), atr_value / closes[-1] if closes[-1] > 0 else 0)
    features.append(atr_normalized)
    
    # Volume features
    volume_ma = pd.Series(volumes).rolling(window=20, min_periods=1).mean().values
    volume_ratio = volumes / (volume_ma + 1e-8)  # Avoid division by zero
    features.append(volume_ratio)
    
    # Stack features
    feature_matrix = np.stack(features, axis=1)
    
    # Replace NaN and Inf with 0
    feature_matrix = np.nan_to_num(feature_matrix, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Clip extreme values to prevent numerical issues
    feature_matrix = np.clip(feature_matrix, -10, 10)
    
    return feature_matrix


def create_sequences(features: np.ndarray, targets: np.ndarray, 
                     sequence_length: int = 60, 
                     prediction_horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create sequences for time series prediction.
    
    Args:
        features: Feature matrix (timesteps, features)
        targets: Target values (timesteps,)
        sequence_length: Number of time steps to use as input
        prediction_horizon: How many steps ahead to predict
        
    Returns:
        X: Input sequences (samples, sequence_length, features)
        y: Target values (samples,)
    """
    if len(features) < sequence_length + prediction_horizon:
        return None, None
    
    X, y = [], []
    
    for i in range(len(features) - sequence_length - prediction_horizon + 1):
        X.append(features[i:i+sequence_length])
        # Predict price change percentage
        current_price = features[i+sequence_length-1, 0]  # First feature is returns
        future_price_idx = i + sequence_length + prediction_horizon - 1
        if future_price_idx < len(features):
            # Target: price return (positive = up, negative = down)
            y.append(targets[future_price_idx])
    
    return np.array(X), np.array(y)


async def collect_training_data(pair: str = 'SOLUSDT', 
                                days: int = 365,
                                interval_minutes: int = 60) -> Tuple[np.ndarray, np.ndarray]:
    """
    Collect historical data for training.
    
    Args:
        pair: Trading pair symbol
        days: Number of days of historical data
        interval_minutes: Candle interval in minutes
        
    Returns:
        X: Feature sequences (samples, sequence_length, features)
        y: Target values (price change direction: 1=up, 0=down, -1=hold)
    """
    logger.info(f"Collecting {days} days of data for {pair}")
    
    # Get historical data
    # Note: Kraken API returns 720 candles max, so we need multiple calls
    all_ohlc = []
    total_candles_needed = (days * 24 * 60) // interval_minutes
    
    # Fetch in batches with better rate limiting
    batches = (total_candles_needed // 720) + 1
    for batch in range(batches):
        try:
            ohlc = await get_historical_data(pair, interval_minutes)
            if ohlc:
                all_ohlc.extend(ohlc)
                logger.info(f"Fetched batch {batch+1}/{batches}, total candles: {len(all_ohlc)}")
            await asyncio.sleep(2.0)  # Increased delay to avoid rate limits
        except Exception as e:
            logger.warning(f"Error fetching batch {batch+1}: {e}")
            await asyncio.sleep(5.0)  # Longer delay on error
            if batch > 5:  # Stop after some successful batches to avoid too many errors
                break
    
    if len(all_ohlc) < 100:
        logger.error(f"Not enough data collected: {len(all_ohlc)} candles")
        return None, None
    
    # Also fetch BTC data for cross-asset features
    btc_ohlc = await get_historical_data('XXBTZUSD', interval_minutes)
    
    logger.info(f"Extracting features from {len(all_ohlc)} candles...")
    
    # Extract features
    features = extract_features(all_ohlc, btc_ohlc)
    if features is None:
        logger.error("Failed to extract features")
        return None, None
    
    # Create targets: price direction
    closes = np.array([float(c[4]) for c in all_ohlc])
    price_changes = np.diff(closes) / closes[:-1]
    
    # Convert to classification: 1=up, 0=down, -1=hold (if small change)
    thresholds = 0.001  # 0.1% threshold
    targets = np.where(price_changes > thresholds, 1.0,
              np.where(price_changes < -thresholds, -1.0, 0.0))
    targets = np.concatenate([[0], targets])  # Pad first element
    
    # Create sequences
    logger.info(f"Creating sequences (sequence_length=60)...")
    X, y = create_sequences(features, targets, sequence_length=60, prediction_horizon=1)
    
    if X is None or len(X) == 0:
        logger.error("Failed to create sequences")
        return None, None
    
    logger.info(f"Created {len(X)} training samples")
    logger.info(f"Feature shape: {X.shape}, Target shape: {y.shape}")
    logger.info(f"Class distribution - Up: {np.sum(y == 1)}, Down: {np.sum(y == -1)}, Hold: {np.sum(y == 0)}")
    
    return X, y

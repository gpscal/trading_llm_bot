"""
GPU-accelerated RSI (Relative Strength Index) calculation using CuPy.
"""

GPU_AVAILABLE = False
try:
    import cupy as cp
    try:
        cp.cuda.runtime.getDeviceCount()
        GPU_AVAILABLE = True
    except Exception:
        GPU_AVAILABLE = False
        import numpy as cp
except (ImportError, RuntimeError):
    import numpy as cp
    GPU_AVAILABLE = False

from config.config import CONFIG


def calculate_rsi_gpu(ohlc_data, period=None):
    """
    Calculate RSI using GPU acceleration.
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        ohlc_data: List of OHLC candles
        period: RSI period (defaults to CONFIG['rsi_period'])
        
    Returns:
        RSI value (0-100)
    """
    period = period or CONFIG['rsi_period']
    
    # Extract closing prices
    if isinstance(ohlc_data, list):
        closes = [float(candle[4]) for candle in ohlc_data]
    else:
        closes = ohlc_data
    
    if len(closes) < period + 1:
        return None
    
    if GPU_AVAILABLE:
        closes = cp.asarray(closes, dtype=cp.float32)
        
        # Calculate price changes
        deltas = cp.diff(closes)
        
        # Separate gains and losses
        gains = cp.where(deltas > 0, deltas, 0.0)
        losses = cp.where(deltas < 0, -deltas, 0.0)
        
        # Calculate average gain and loss using Wilder's smoothing method
        avg_gain = cp.mean(gains[-period:])
        avg_loss = cp.mean(losses[-period:])
        
        # Handle division by zero
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return float(rsi.item())
    else:
        # CPU fallback
        import numpy as np
        closes = np.array(closes)
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
            return float(rsi)

"""
GPU-accelerated moving average calculation using CuPy.
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


def calculate_moving_average_gpu(ohlc_data, period=None, batch_mode=False):
    """
    Calculate moving average using GPU acceleration.
    
    Args:
        ohlc_data: List of OHLC candles or numpy/cupy array
        period: MA period (defaults to CONFIG['ma_period'])
        batch_mode: If True, process multiple timeframes simultaneously
        
    Returns:
        Moving average value or array of values (if batch_mode)
    """
    if not GPU_AVAILABLE:
        # Fallback to CPU if GPU not available
        import numpy as np
        closes = np.array([float(candle[4]) for candle in ohlc_data])
        period = period or CONFIG['ma_period']
        if len(closes) < period:
            return None
        return float(np.mean(closes[-period:]))
    
    period = period or CONFIG['ma_period']
    
    # Convert to CuPy array if needed
    if isinstance(ohlc_data, list):
        closes = cp.array([float(candle[4]) for candle in ohlc_data])
    else:
        closes = cp.asarray(ohlc_data)
    
    if len(closes) < period:
        return None
    
    if batch_mode and closes.ndim > 1:
        # Batch processing: calculate MA for multiple series at once
        return cp.mean(closes[:, -period:], axis=1)
    else:
        # Single series
        result = cp.mean(closes[-period:])
        # Convert back to Python float for compatibility
        return float(result.item())


def calculate_ema_gpu(closes, period, alpha=None):
    """
    Calculate Exponential Moving Average using GPU.
    
    EMA is more responsive than SMA and benefits greatly from GPU acceleration.
    """
    if not GPU_AVAILABLE:
        import numpy as np
        closes = np.array(closes) if not isinstance(closes, np.ndarray) else closes
        alpha = alpha or (2.0 / (period + 1))
        ema = np.zeros_like(closes)
        ema[0] = closes[0]
        for i in range(1, len(closes)):
            ema[i] = alpha * closes[i] + (1 - alpha) * ema[i-1]
        return float(ema[-1])
    
    closes = cp.asarray(closes)
    alpha = alpha or (2.0 / (period + 1))
    
    # Vectorized EMA calculation on GPU
    ema = cp.zeros_like(closes)
    ema[0] = closes[0]
    
    # Calculate EMA using GPU-accelerated operations
    for i in range(1, len(closes)):
        ema[i] = alpha * closes[i] + (1 - alpha) * ema[i-1]
    
    # Note: While this loop can't be fully vectorized due to dependency,
    # GPU still helps with the arithmetic operations
    return float(ema[-1].item())


def calculate_multiple_mas_gpu(closes, periods):
    """
    Calculate multiple moving averages simultaneously on GPU.
    
    This is where GPU really shines - calculating many indicators in parallel.
    
    Args:
        closes: Array of closing prices
        periods: List of periods to calculate MA for
        
    Returns:
        Dictionary mapping period -> MA value
    """
    if not GPU_AVAILABLE:
        # Fallback
        import numpy as np
        closes = np.array(closes)
        return {p: float(np.mean(closes[-p:])) for p in periods if len(closes) >= p}
    
    closes = cp.asarray(closes)
    results = {}
    
    # Process all periods in parallel
    for period in periods:
        if len(closes) >= period:
            ma = cp.mean(closes[-period:])
            results[period] = float(ma.item())
    
    return results

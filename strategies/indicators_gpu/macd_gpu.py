"""
GPU-accelerated MACD calculation using CuPy.
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


def calculate_ema_gpu(closes, period):
    """Calculate Exponential Moving Average on GPU."""
    if not GPU_AVAILABLE:
        # CPU fallback
        import numpy as np
        closes = np.array(closes)
        alpha = 2.0 / (period + 1)
        ema = np.zeros(len(closes))
        ema[0] = closes[0]
        for i in range(1, len(closes)):
            ema[i] = alpha * closes[i] + (1 - alpha) * ema[i-1]
        return ema
    else:
        closes = cp.asarray(closes)
        alpha = cp.float32(2.0 / (period + 1))
        ema = cp.zeros(len(closes), dtype=cp.float32)
        ema[0] = closes[0]
        
        # GPU-accelerated EMA calculation
        for i in range(1, len(closes)):
            ema[i] = alpha * closes[i] + (1 - alpha) * ema[i-1]
        
        return ema


def calculate_macd_gpu(ohlc_data, 
                       fast_period=None, 
                       slow_period=None, 
                       signal_period=None):
    """
    Calculate MACD (Moving Average Convergence Divergence) using GPU acceleration.
    
    Args:
        ohlc_data: List of OHLC candles
        fast_period: Fast EMA period (defaults to CONFIG['macd_fast_period'])
        slow_period: Slow EMA period (defaults to CONFIG['macd_slow_period'])
        signal_period: Signal line EMA period (defaults to CONFIG['macd_signal_period'])
        
    Returns:
        Tuple of (MACD line value, Signal line value)
    """
    fast_period = fast_period or CONFIG['macd_fast_period']
    slow_period = slow_period or CONFIG['macd_slow_period']
    signal_period = signal_period or CONFIG['macd_signal_period']
    
    # Extract closing prices
    if isinstance(ohlc_data, list):
        closes = [float(candle[4]) for candle in ohlc_data]
    else:
        closes = ohlc_data
    
    if len(closes) < slow_period:
        return None, None
    
    # Calculate EMAs on GPU
    fast_ema = calculate_ema_gpu(closes, fast_period)
    slow_ema = calculate_ema_gpu(closes, slow_period)
    
    if GPU_AVAILABLE:
        # MACD line = Fast EMA - Slow EMA
        macd_line = fast_ema[-1] - slow_ema[-1]
        
        # Calculate MACD history for signal line
        # For signal, we need the difference over time
        macd_values = fast_ema - slow_ema
        
        # Signal line is EMA of MACD line
        signal_ema = calculate_ema_gpu(macd_values, signal_period)
        signal_line = signal_ema[-1]
        
        return float(macd_line.item()), float(signal_line.item())
    else:
        # CPU fallback
        macd_line = float(fast_ema[-1] - slow_ema[-1])
        macd_values = fast_ema - slow_ema
        signal_ema = calculate_ema_gpu(macd_values, signal_period)
        signal_line = float(signal_ema[-1])
        
        return macd_line, signal_line

"""
GPU-accelerated Bollinger Bands calculation using CuPy.
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


def calculate_bollinger_bands_gpu(ohlc_data, period=None, num_std=2):
    """
    Calculate Bollinger Bands using GPU acceleration.
    
    Bollinger Bands consist of:
    - Middle Band: Simple Moving Average
    - Upper Band: SMA + (num_std * standard deviation)
    - Lower Band: SMA - (num_std * standard deviation)
    
    Args:
        ohlc_data: List of OHLC candles
        period: MA period (defaults to CONFIG['bb_period'])
        num_std: Number of standard deviations for bands (default: 2)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    period = period or CONFIG['bb_period']
    
    # Extract closing prices
    if isinstance(ohlc_data, list):
        closes = [float(candle[4]) for candle in ohlc_data]
    else:
        closes = ohlc_data
    
    if len(closes) < period:
        return None, None, None
    
    if GPU_AVAILABLE:
        try:
            closes = cp.asarray(closes[-period:], dtype=cp.float32)
            
            # Calculate SMA (middle band)
            middle_band = cp.mean(closes)
            
            # Calculate standard deviation
            std = cp.std(closes)
            
            # Calculate upper and lower bands
            upper_band = middle_band + (num_std * std)
            lower_band = middle_band - (num_std * std)
            
            return (
                float(upper_band.item()),
                float(middle_band.item()),
                float(lower_band.item())
            )
        except Exception:
            # Fallback to CPU on error
            GPU_AVAILABLE = False
            import numpy as np
            closes = np.array(closes[-period:])
            middle_band = np.mean(closes)
            std = np.std(closes)
            
            upper_band = middle_band + (num_std * std)
            lower_band = middle_band - (num_std * std)
            
            return (
                float(upper_band),
                float(middle_band),
                float(lower_band)
            )
    else:
        # CPU fallback
        import numpy as np
        closes = np.array(closes[-period:])
        middle_band = np.mean(closes)
        std = np.std(closes)
        
        upper_band = middle_band + (num_std * std)
        lower_band = middle_band - (num_std * std)
        
        return (
            float(upper_band),
            float(middle_band),
            float(lower_band)
        )

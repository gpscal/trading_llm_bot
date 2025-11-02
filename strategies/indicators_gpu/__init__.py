"""
GPU-accelerated indicator calculations using CuPy.

This module provides drop-in replacements for CPU-based indicators
with GPU acceleration for 10-50x performance improvement.
"""

GPU_AVAILABLE = False
cp = None  # Will be set to either cupy or numpy

try:
    import cupy as cp
    # Test if CUDA is actually available (not just CuPy installed)
    if cp.cuda.is_available():
        try:
            # Try to get device count - this will fail if CUDA runtime isn't accessible
            device_count = cp.cuda.runtime.getDeviceCount()
            if device_count > 0:
                GPU_AVAILABLE = True
        except Exception as e:
            # CuPy installed but CUDA runtime not accessible
            GPU_AVAILABLE = False
            import numpy as cp  # Fallback to NumPy
    else:
        GPU_AVAILABLE = False
        import numpy as cp  # Fallback to NumPy
except (ImportError, RuntimeError) as e:
    # CuPy not installed or failed to load
    GPU_AVAILABLE = False
    import numpy as cp  # Fallback to NumPy if CuPy not available

from .moving_average_gpu import calculate_moving_average_gpu
from .macd_gpu import calculate_macd_gpu
from .rsi_gpu import calculate_rsi_gpu
from .bollinger_bands_gpu import calculate_bollinger_bands_gpu
from .indicators_gpu import calculate_indicators_gpu

__all__ = [
    'GPU_AVAILABLE',
    'calculate_moving_average_gpu',
    'calculate_macd_gpu',
    'calculate_rsi_gpu',
    'calculate_bollinger_bands_gpu',
    'calculate_indicators_gpu',
]

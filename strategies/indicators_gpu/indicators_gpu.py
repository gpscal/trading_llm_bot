"""
GPU-accelerated indicator calculation coordinator.
"""

from .moving_average_gpu import calculate_moving_average_gpu
from .macd_gpu import calculate_macd_gpu
from .rsi_gpu import calculate_rsi_gpu
from .bollinger_bands_gpu import calculate_bollinger_bands_gpu
from ..indicators.atr import calculate_atr
from ..indicators.correlation import calculate_correlation
from ..indicators.stochastic_oscillator import calculate_stochastic_oscillator
from ..indicators.adx import calculate_adx
from ..indicators.obv import calculate_obv
from ..indicators.momentum import calculate_momentum


def calculate_indicators_gpu(btc_historical, sol_historical):
    """
    Calculate all indicators using GPU acceleration where available.
    
    This function coordinates GPU-accelerated indicator calculations
    while falling back to CPU for indicators not yet GPU-optimized.
    
    Args:
        btc_historical: BTC historical OHLC data
        sol_historical: SOL historical OHLC data
        
    Returns:
        Tuple of (btc_indicators, sol_indicators) dictionaries
    """
    # GPU-accelerated indicators
    btc_indicators = {
        'moving_avg': calculate_moving_average_gpu(btc_historical),
        'bollinger_bands': calculate_bollinger_bands_gpu(btc_historical),
        'macd': calculate_macd_gpu(btc_historical),
        'rsi': calculate_rsi_gpu(btc_historical),
    }
    
    sol_indicators = {
        'moving_avg': calculate_moving_average_gpu(sol_historical),
        'bollinger_bands': calculate_bollinger_bands_gpu(sol_historical),
        'macd': calculate_macd_gpu(sol_historical),
        'rsi': calculate_rsi_gpu(sol_historical),
    }
    
    # CPU-based indicators (can be GPU-accelerated later)
    btc_indicators.update({
        'atr': calculate_atr(btc_historical),
        'correlation': calculate_correlation(btc_historical, sol_historical),
        'stochastic_oscillator': calculate_stochastic_oscillator(btc_historical),
        'momentum': calculate_momentum(btc_historical),
        'adx': calculate_adx(btc_historical),
        'obv': calculate_obv(btc_historical),
    })
    
    sol_indicators.update({
        'atr': calculate_atr(sol_historical),
        'correlation': calculate_correlation(sol_historical, btc_historical),
        'stochastic_oscillator': calculate_stochastic_oscillator(sol_historical),
        'momentum': calculate_momentum(sol_historical),
        'adx': calculate_adx(sol_historical),
        'obv': calculate_obv(sol_historical),
    })
    
    return btc_indicators, sol_indicators

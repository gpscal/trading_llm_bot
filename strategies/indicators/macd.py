import numpy as np
from config.config import CONFIG

def calculate_macd(ohlc_data, fast_period=CONFIG['macd_fast_period'], slow_period=CONFIG['macd_slow_period'], signal_period=CONFIG['macd_signal_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < slow_period:
        return None, None
    fast_ema = np.mean(closes[-fast_period:])
    slow_ema = np.mean(closes[-slow_period:])
    macd = fast_ema - slow_ema
    signal = np.mean(closes[-signal_period:])
    return macd, signal

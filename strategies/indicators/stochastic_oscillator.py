import numpy as np
from config.config import CONFIG

def calculate_stochastic_oscillator(ohlc_data, period=CONFIG['stochastic_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    lows = np.array([float(candle[3]) for candle in ohlc_data])
    highs = np.array([float(candle[2]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    lowest_low = np.min(lows[-period:])
    highest_high = np.max(highs[-period:])
    return (closes[-1] - lowest_low) / (highest_high - lowest_low) * 100

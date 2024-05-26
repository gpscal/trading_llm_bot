import numpy as np
from config.config import CONFIG

def calculate_bollinger_bands(ohlc_data, period=CONFIG['bb_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    sma = np.mean(closes[-period:])
    std_dev = np.std(closes[-period:])
    upper_band = sma + (std_dev * 2)
    lower_band = sma - (std_dev * 2)
    return upper_band, lower_band

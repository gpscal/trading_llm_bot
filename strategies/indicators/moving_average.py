import numpy as np
from config.config import CONFIG

def calculate_moving_average(ohlc_data, period=CONFIG['ma_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    return np.mean(closes[-period:])

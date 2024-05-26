import numpy as np
from config.config import CONFIG

def calculate_atr(ohlc_data, period=CONFIG['atr_period']):
    highs = np.array([float(candle[2]) for candle in ohlc_data])
    lows = np.array([float(candle[3]) for candle in ohlc_data])
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(highs) != len(lows) or len(lows) != len(closes):
        return None

    prev_close = np.roll(closes, 1)
    prev_close[0] = closes[0]
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - prev_close), np.abs(lows - prev_close)))
    
    atr = np.zeros_like(tr)
    atr[0] = np.mean(tr[:period])
    for i in range(1, len(tr)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

    return atr[-1]

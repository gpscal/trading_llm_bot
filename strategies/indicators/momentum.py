import numpy as np

def calculate_momentum(ohlc_data, period=14):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    return closes[-1] - closes[-period]

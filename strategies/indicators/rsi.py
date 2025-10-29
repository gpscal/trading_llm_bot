import numpy as np
from config.config import CONFIG

def calculate_rsi(ohlc_data, period=CONFIG['rsi_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    deltas = np.diff(closes)
    gains = deltas[deltas > 0].sum() / period
    losses = -deltas[deltas < 0].sum() / period
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

import numpy as np
from config.config import CONFIG

def calculate_adx(ohlc_data, period=CONFIG['adx_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    highs = np.array([float(candle[2]) for candle in ohlc_data])
    lows = np.array([float(candle[3]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    up_moves = highs[1:] - highs[:-1]
    down_moves = lows[:-1] - lows[1:]
    plus_dm = np.where((up_moves > down_moves) & (up_moves > 0), up_moves, 0)
    minus_dm = np.where((down_moves > up_moves) & (down_moves > 0), down_moves, 0)
    tr = np.maximum(highs[1:], closes[:-1]) - np.minimum(lows[1:], closes[:-1])
    atr = np.zeros_like(tr)
    atr[0] = np.mean(tr[:period])
    for i in range(1, len(tr)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    plus_di = 100 * (np.cumsum(plus_dm) / atr)
    minus_di = 100 * (np.cumsum(minus_dm) / atr)
    dx = np.zeros_like(plus_di)
    non_zero_indices = (plus_di + minus_di) != 0
    dx[non_zero_indices] = 100 * np.abs(plus_di[non_zero_indices] - minus_di[non_zero_indices]) / (plus_di[non_zero_indices] + minus_di[non_zero_indices])
    dx[np.isnan(dx)] = 0  # Avoid NaN values
    adx = np.zeros_like(dx)
    adx[0] = np.mean(dx[:period])
    for i in range(1, len(dx)):
        adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
    return adx[-1]

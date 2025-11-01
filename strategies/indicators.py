# strategies/indicators.py

import numpy as np
from config.config import CONFIG

def calculate_moving_average(ohlc_data, period=CONFIG['ma_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    return np.mean(closes[-period:])

def calculate_bollinger_bands(ohlc_data, period=CONFIG['bb_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    sma = np.mean(closes[-period:])
    std_dev = np.std(closes[-period:])
    upper_band = sma + (std_dev * 2)
    lower_band = sma - (std_dev * 2)
    return upper_band, lower_band

def calculate_macd(ohlc_data, fast_period=CONFIG['macd_fast_period'], slow_period=CONFIG['macd_slow_period'], signal_period=CONFIG['macd_signal_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < slow_period:
        return None, None
    fast_ema = np.mean(closes[-fast_period:])
    slow_ema = np.mean(closes[-slow_period:])
    macd = fast_ema - slow_ema
    signal = np.mean(closes[-signal_period:])
    return macd, signal

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

def calculate_correlation(btc_data, sol_data):
    btc_closes = np.array([float(candle[4]) for candle in btc_data])
    sol_closes = np.array([float(candle[4]) for candle in sol_data])
    min_length = min(len(btc_closes), len(sol_closes))
    btc_closes = btc_closes[:min_length]
    sol_closes = sol_closes[:min_length]
    correlation = np.corrcoef(btc_closes, sol_closes)[0, 1]
    return correlation

def calculate_stochastic_oscillator(ohlc_data, period=CONFIG['stochastic_period']):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    lows = np.array([float(candle[3]) for candle in ohlc_data])
    highs = np.array([float(candle[2]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    lowest_low = np.min(lows[-period:])
    highest_high = np.max(highs[-period:])
    return (closes[-1] - lowest_low) / (highest_high - lowest_low) * 100

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
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    dx[np.isnan(dx)] = 0  # Avoid NaN values
    adx = np.zeros_like(dx)
    adx[0] = np.mean(dx[:period])
    for i in range(1, len(dx)):
        adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
    return adx[-1]


def calculate_obv(ohlc_data):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    volumes = np.array([float(candle[5]) for candle in ohlc_data])
    obv = np.zeros_like(closes)
    obv[0] = volumes[0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv[i] = obv[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv[i] = obv[i - 1] - volumes[i]
        else:
            obv[i] = obv[i - 1]
    return obv[-1]

def calculate_momentum(ohlc_data, period=14):
    closes = np.array([float(candle[4]) for candle in ohlc_data])
    if len(closes) < period:
        return None
    return closes[-1] - closes[-period]

def calculate_indicators(btc_historical, sol_historical):
    btc_indicators = {
        'moving_avg': calculate_moving_average(btc_historical),
        'bollinger_bands': calculate_bollinger_bands(btc_historical),
        'macd': calculate_macd(btc_historical),
        'rsi': calculate_rsi(btc_historical),
        'atr': calculate_atr(btc_historical),
        'correlation': calculate_correlation(btc_historical, sol_historical),
        'stochastic_oscillator': calculate_stochastic_oscillator(btc_historical),
        'momentum': calculate_momentum(btc_historical),
        'adx': calculate_adx(btc_historical),
        'obv': calculate_obv(btc_historical)
    }
    sol_indicators = {
        'moving_avg': calculate_moving_average(sol_historical),
        'bollinger_bands': calculate_bollinger_bands(sol_historical),
        'macd': calculate_macd(sol_historical),
        'rsi': calculate_rsi(sol_historical),
        'atr': calculate_atr(sol_historical),
        'correlation': calculate_correlation(sol_historical, btc_historical),
        'stochastic_oscillator': calculate_stochastic_oscillator(sol_historical),
        'momentum': calculate_momentum(sol_historical),
        'adx': calculate_adx(sol_historical),
        'obv': calculate_obv(sol_historical)
    }

    return btc_indicators, sol_indicators

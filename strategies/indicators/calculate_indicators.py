from .moving_average import calculate_moving_average
from .bollinger_bands import calculate_bollinger_bands
from .macd import calculate_macd
from .rsi import calculate_rsi
from .atr import calculate_atr
from .correlation import calculate_correlation
from .stochastic_oscillator import calculate_stochastic_oscillator
from .adx import calculate_adx
from .obv import calculate_obv
from .momentum import calculate_momentum

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

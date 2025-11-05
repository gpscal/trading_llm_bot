from strategies.indicators import calculate_indicators  # Import the calculate_indicators function
from utils.logger import setup_logger

logger = setup_logger('trade_utils_logger', 'trade_utils.log')


def analyze_historical_data(historical_map):
    """Return indicator map keyed by coin symbol (expects BTC and SOL)."""

    btc_historical = historical_map.get('BTC')
    sol_historical = historical_map.get('SOL')
    if not btc_historical or not sol_historical:
        raise ValueError("Historical data for both BTC and SOL is required to compute indicators")

    btc_indicators, sol_indicators = calculate_indicators(btc_historical, sol_historical)
    return {
        'BTC': btc_indicators,
        'SOL': sol_indicators,
    }

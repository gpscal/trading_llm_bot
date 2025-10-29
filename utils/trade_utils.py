from strategies.indicators import calculate_indicators  # Import the calculate_indicators function
from trade.trade_logic import handle_trade_with_fees
from utils.utils import log_and_print_status
from utils.logger import setup_logger

logger = setup_logger('trade_utils_logger', 'trade_utils.log')

def analyze_historical_data(btc_historical, sol_historical):
    btc_indicators, sol_indicators = calculate_indicators(btc_historical, sol_historical)
    return btc_indicators, sol_indicators

async def common_trade_handler(ticker_fetcher, pairs, balance, btc_indicators, sol_indicators):
    try:
        btc_ticker = await ticker_fetcher(pairs['btc'])
        sol_ticker = await ticker_fetcher(pairs['sol'])
        if not btc_ticker or not sol_ticker:
            logger.error("Failed to fetch ticker data.")
            return
        btc_price = float(btc_ticker['c'][0])
        sol_price = float(sol_ticker['c'][0])
        balance['btc_price'] = btc_price
        balance['sol_price'] = sol_price
        balance['usdt'], balance['sol'], balance['last_trade_time'] = handle_trade_with_fees(
            btc_price, sol_price, balance['usdt'], balance['sol'], balance['last_trade_time'], btc_indicators, sol_indicators, balance['sol_price'], balance['initial_total_usd']
        )
        current_total_usd = balance['usdt'] + balance['sol'] * sol_price
        total_gain_usd = current_total_usd - balance['initial_total_usd']
        log_and_print_status(balance, current_total_usd, total_gain_usd)
    except Exception as e:
        logger.error(f"Error in common_trade_handler: {e}")

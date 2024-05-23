import asyncio
from api.kraken import get_ticker
from utils.trade_utils import common_trade_handler, initialize_balances
from config.config import CONFIG
from utils.logger import setup_logger
from utils.data_fetchers import fetch_initial_sol_price, fetch_and_analyze_historical_data  # Import shared functions
import logging

logger = setup_logger('live_trade_logger', 'live_trade.log')

async def live_trade():
    pairs = {
        'btc': 'XXBTZUSD',
        'sol': 'SOLUSDT'
    }
    balance = await initialize_balances()

    sol_initial_price = await fetch_initial_sol_price()
    initial_total_usd = balance['usdt'] + balance['sol'] * sol_initial_price
    balance['initial_total_usd'] = initial_total_usd  # Store initial total USD in balance dictionary

    await fetch_and_analyze_historical_data(pairs, balance)  # Initial fetch and analysis

    while True:
        await common_trade_handler(get_ticker, pairs, balance, balance['btc_indicators'], balance['sol_indicators'])
        await asyncio.sleep(CONFIG['poll_interval'])  # Poll interval between trades
        await fetch_and_analyze_historical_data(pairs, balance)  # Periodically update historical data and indicators

if __name__ == '__main__':
    logger.info("Starting live trading")
    asyncio.run(live_trade())

import asyncio
from api.kraken import get_ticker
from utils.trade_utils import common_trade_handler, initialize_balances
from config.config import CONFIG
from utils.logger import setup_logger
from utils.data_fetchers import fetch_initial_sol_price, fetch_and_analyze_historical_data
import logging
from utils.shared_state import update_bot_state

logger = setup_logger('live_trade_logger', 'live_trade.log')

async def live_trade():
    pairs = {
        'btc': 'XXBTZUSD',
        'sol': 'SOLUSDT'
    }
    balance = await initialize_balances()

    # Ensuring SOL initial price is only fetched once
    sol_initial_price = balance['sol_price']
    logger.info(f"Initial SOL price used: {sol_initial_price}")

    initial_total_usd = balance['usdt'] + balance['sol'] * sol_initial_price
    balance['initial_total_usd'] = initial_total_usd

    await fetch_and_analyze_historical_data(pairs, balance)

    logger.info(f"Initial Balances: USDT: {balance['usdt']}, SOL: {balance['sol']}, Initial Total USD: {balance['initial_total_usd']}")

    # Update shared state
    update_bot_state({"balance": balance, "indicators": {"btc": balance['btc_indicators'], "sol": balance['sol_indicators']}})

    while True:
        await common_trade_handler(get_ticker, pairs, balance, balance['btc_indicators'], balance['sol_indicators'])
        await asyncio.sleep(CONFIG['poll_interval'])
        await fetch_and_analyze_historical_data(pairs, balance)
        update_bot_state({"balance": balance})  # Update after each cycle

if __name__ == '__main__':
    logger.info("Starting live trading")
    asyncio.run(live_trade())

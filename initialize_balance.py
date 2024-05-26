from utils.data_fetchers import fetch_initial_sol_price
from config.config import CONFIG
import logging

logger = logging.getLogger('initialize_balance')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('initialize_balance.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def initialize_balance():
    sol_initial_price = await fetch_initial_sol_price()
    print("Initial SOL price fetched")
    logger.info("Initial SOL price fetched")

    balance = {
        'usdt': CONFIG['initial_balance_usdt'],
        'sol': CONFIG['initial_balance_sol'],
        'sol_price': sol_initial_price,
        'btc_price': None,
        'btc_momentum': 0.0,
        'confidence': 0.0,
        'initial_total_usd': None,
        'last_trade_time': 0,
        'btc_indicators': None,
        'sol_indicators': None
    }
    initial_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
    balance['initial_total_usd'] = round(initial_total_usd, 2)

    logger.info(f"Initial SOL Price: {sol_initial_price}")
    logger.info(f"Initial Total USD (before rounding): {initial_total_usd}")
    logger.info(f"Initial Total USD (after rounding): {balance['initial_total_usd']}")

    print(f"Initial Balance: {balance}")
    return balance

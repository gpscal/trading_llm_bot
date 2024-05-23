import asyncio
from api.kraken import get_ticker, get_historical_data
from utils.trade_utils import common_trade_handler, initialize_balances, analyze_historical_data
from config.config import CONFIG
from utils.logger import setup_logger
import aiohttp

logger = setup_logger('live_trade_logger', 'live_trade.log')

async def fetch_initial_sol_price():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.kraken.com/0/public/Ticker?pair=SOLUSD") as response:
            data = await response.json()
            return float(data['result']['SOLUSD']['c'][0])

async def live_trade():
    pairs = {
        'btc': 'XXBTZUSD',
        'sol': 'SOLUSDT'
    }
    balance = await initialize_balances()

    sol_initial_price = await fetch_initial_sol_price()
    initial_total_usd = balance['usdt'] + balance['sol'] * sol_initial_price
    balance['initial_total_usd'] = initial_total_usd  # Store initial total USD in balance dictionary

    btc_historical = await get_historical_data(pairs['btc'], 60)
    sol_historical = await get_historical_data(pairs['sol'], 60)

    if btc_historical and sol_historical:
        btc_indicators, sol_indicators = analyze_historical_data(btc_historical, sol_historical)
        logger.info(f"BTC Indicators: {btc_indicators}")
        logger.info(f"SOL Indicators: {sol_indicators}")

    await common_trade_handler(get_ticker, pairs, balance, btc_indicators, sol_indicators)

if __name__ == '__main__':
    logger.info("Starting live trading")
    asyncio.run(live_trade())

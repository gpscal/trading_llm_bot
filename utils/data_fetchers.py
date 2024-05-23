import aiohttp
from api.kraken import get_historical_data
from utils.trade_utils import analyze_historical_data
import logging

logger = logging.getLogger('data_fetchers_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('data_fetchers.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def fetch_initial_sol_price():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.kraken.com/0/public/Ticker?pair=SOLUSD") as response:
            data = await response.json()
            sol_price = float(data['result']['SOLUSD']['c'][0])
            logger.info(f"Fetched Initial SOL Price: {sol_price}")
            return sol_price

async def fetch_and_analyze_historical_data(pairs, balance):
    btc_historical = await get_historical_data(pairs['btc'], 60)
    sol_historical = await get_historical_data(pairs['sol'], 60)
    btc_indicators, sol_indicators = None, None
    if btc_historical and sol_historical:
        btc_indicators, sol_indicators = analyze_historical_data(btc_historical, sol_historical)
        logger.info(f"BTC Indicators: {btc_indicators}")
        logger.info(f"SOL Indicators: {sol_indicators}")
    balance['btc_indicators'] = btc_indicators
    balance['sol_indicators'] = sol_indicators

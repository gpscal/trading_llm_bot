import aiohttp
import logging
import time
import asyncio
from typing import Dict

from api.kraken import get_historical_data
from utils.trade_utils import analyze_historical_data
from utils.coin_pair_manager import get_coin_pair_manager

logger = logging.getLogger('data_fetchers_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('data_fetchers.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

_pair_manager = get_coin_pair_manager()

# Cache for historical data to avoid rate limiting
# Format: {coin: {'data': [...], 'timestamp': float, 'pair': str}}
_historical_data_cache: Dict[str, Dict[str, float | list]] = {}
_cache_duration = 300  # Cache for 5 minutes (300 seconds) - reduces API calls significantly

# Last known prices to provide graceful degradation when the API misbehaves
_last_known_prices: Dict[str, float] = {}


async def _fetch_ticker(pair: str) -> dict | None:
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            if data.get('error'):
                logger.error(f"Error fetching ticker for {pair}: {data['error']}")
                return None
            return data.get('result', {}).get(pair)


async def fetch_initial_price(
    coin: str,
    retries: int = 3,
    initial_backoff: float = 1.0,
    prefer_usdt: bool = True
) -> float | None:
    """Fetch the latest price for a coin with retry/backoff and cached fallback."""

    coin = _pair_manager.validate_coin(coin)
    backoff = initial_backoff
    last_known_price = _last_known_prices.get(coin)

    for attempt in range(1, retries + 1):
        pair = _pair_manager.get_rest_pair(coin, prefer_usdt=prefer_usdt)
        alt_pair = _pair_manager.get_rest_pair(coin, prefer_usdt=not prefer_usdt)
        pairs_to_try = [pair]
        if alt_pair not in pairs_to_try:
            pairs_to_try.append(alt_pair)

        for current_pair in pairs_to_try:
            try:
                ticker = await _fetch_ticker(current_pair)
                if ticker:
                    price = float(ticker['c'][0])
                    logger.info(f"Fetched initial {coin} price {price} from {current_pair}")
                    _last_known_prices[coin] = price
                    return price
            except Exception as exc:
                logger.error(f"Attempt {attempt} - Error fetching {coin} price from {current_pair}: {exc}")
                print(f"Attempt {attempt} - Error fetching {coin} price from {current_pair}: {exc}")

        if attempt < retries:
            await asyncio.sleep(backoff)
            backoff *= 2

    if last_known_price is not None:
        logger.warning(
            "Falling back to last known %s price %.2f after %d failed attempts",
            coin,
            last_known_price,
            retries,
        )
        return last_known_price

    logger.error("Failed to fetch initial %s price after %d attempts and no cached price available", coin, retries)
    return None


async def fetch_initial_sol_price(retries: int = 3, initial_backoff: float = 1.0) -> float | None:
    """Backward-compatible wrapper to fetch the SOL price."""

    return await fetch_initial_price('SOL', retries=retries, initial_backoff=initial_backoff, prefer_usdt=False)

async def fetch_and_analyze_historical_data(pairs, balance, interval: int = 60):
    """
    Fetch and analyze historical data with caching to avoid rate limiting.
    
    Uses a cache that refreshes every 5 minutes to dramatically reduce API calls.
    """
    global _historical_data_cache

    current_time = time.time()
    historical_map: Dict[str, list] = {}

    try:
        for coin, pair in pairs.items():
            coin_upper = coin.upper()
            cache_entry = _historical_data_cache.get(coin_upper)
            needs_refresh = (
                cache_entry is None
                or (current_time - cache_entry['timestamp']) > _cache_duration
                or cache_entry.get('pair') != pair
            )

            historical = None
            if needs_refresh:
                logger.info(f"Fetching fresh {coin_upper} historical data (cache expired or missing)")
                historical = await get_historical_data(pair, interval)
                if historical:
                    _historical_data_cache[coin_upper] = {
                        'data': historical,
                        'timestamp': current_time,
                        'pair': pair,
                    }
                    logger.info(f"Cached {coin_upper} data: {len(historical)} candles")
                elif cache_entry:
                    logger.warning(f"{coin_upper} fetch failed, using cached data")
                    historical = cache_entry['data']
            else:
                historical = cache_entry['data']
                cache_age = int(current_time - cache_entry['timestamp'])
                logger.debug(f"Using cached {coin_upper} data (age: {cache_age}s)")

            if not historical:
                logger.warning(f"No historical data available for {coin_upper}")
                continue

            historical_map[coin_upper] = historical

            # Respect Kraken rate limits between sequential requests
            if needs_refresh:
                await asyncio.sleep(1.0)

        if len(historical_map) < 2:
            logger.warning("Insufficient historical data to compute multi-coin indicators")
            return

        indicators_map = analyze_historical_data(historical_map)
        balance.setdefault('coins', {})
        balance.setdefault('indicators', {})

        for coin_upper, indicators in indicators_map.items():
            coin_state = balance['coins'].setdefault(coin_upper, {
                'amount': 0.0,
                'price': 0.0,
                'indicators': {},
                'historical': [],
                'position_entry_price': None,
                'trailing_high_price': None,
            })
            coin_state['indicators'] = indicators or {}
            if historical_map.get(coin_upper):
                coin_state['historical'] = historical_map[coin_upper][:100]
            balance['indicators'][coin_upper.lower()] = indicators or {}

    except Exception as e:
        logger.error(f"Error in fetch_and_analyze_historical_data: {e}")
        print(f"Error in fetch_and_analyze_historical_data: {e}")

        # Try to use cached data on error
        if _historical_data_cache:
            logger.warning("Error occurred, attempting to use cached data")
            try:
                historical_map = {coin: entry['data'] for coin, entry in _historical_data_cache.items() if entry.get('data')}
                if len(historical_map) >= 2:
                    indicators_map = analyze_historical_data(historical_map)
                    for coin_upper, indicators in indicators_map.items():
                        coin_state = balance.setdefault('coins', {}).setdefault(coin_upper, {
                            'amount': 0.0,
                            'price': 0.0,
                            'indicators': {},
                            'historical': [],
                            'position_entry_price': None,
                            'trailing_high_price': None,
                        })
                        coin_state['indicators'] = indicators or {}
                        coin_state['historical'] = historical_map[coin_upper][:100]
                        balance.setdefault('indicators', {})[coin_upper.lower()] = indicators or {}
                    logger.info("Successfully used cached data after error")
            except Exception as cache_error:
                logger.error(f"Failed to use cached data: {cache_error}")

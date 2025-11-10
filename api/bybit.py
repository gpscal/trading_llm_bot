"""
Bybit API Integration
Handles all Bybit API calls with HMAC authentication
"""

import time
import hmac
import hashlib
import aiohttp
from urllib.parse import urlencode
from config.config import CONFIG
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.logger import setup_logger

logger = setup_logger('bybit_api_logger', 'bybit_api.log')


def get_signature(params, secret):
    """Generate HMAC SHA256 signature for Bybit API"""
    # Bybit requires parameters sorted alphabetically
    param_str = urlencode(sorted(params.items()))
    signature = hmac.new(
        secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_balance():
    """
    Fetch account balance from Bybit
    Returns dict with coin balances
    """
    url = CONFIG['bybit_base_url'] + '/v5/account/wallet-balance'
    timestamp = str(int(time.time() * 1000))
    
    params = {
        'api_key': CONFIG['api_key'],
        'timestamp': timestamp,
        'accountType': 'UNIFIED'  # Unified Trading Account
    }
    
    # Generate signature
    params['sign'] = get_signature(params, CONFIG['api_secret'])
    
    headers = {
        'X-BAPI-API-KEY': CONFIG['api_key'],
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-SIGN': params['sign'],
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching balance from Bybit")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response_text = await response.text()
                logger.info(f"Response: {response_text}")
                
                data = await response.json()
                
                if data.get('retCode') == 0:
                    # Success - parse balance
                    result = data.get('result', {})
                    wallet_list = result.get('list', [])
                    
                    if not wallet_list:
                        logger.warning("No wallet data returned")
                        return {}
                    
                    # Parse balances from wallet
                    balances = {}
                    wallet = wallet_list[0]
                    coins = wallet.get('coin', [])
                    
                    for coin_data in coins:
                        coin = coin_data.get('coin')
                        available = float(coin_data.get('availableToWithdraw', 0))
                        
                        if available > 0:
                            balances[coin] = available
                    
                    logger.info(f"Balances: {balances}")
                    return balances
                else:
                    error_msg = data.get('retMsg', 'Unknown error')
                    logger.error(f"Bybit API error: {error_msg}")
                    return {'error': [error_msg]}
                    
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        return {'error': [str(e)]}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_ticker(symbol):
    """
    Fetch current ticker price for a symbol
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT', 'SOLUSDT')
    
    Returns:
        dict with ticker data
    """
    url = CONFIG['bybit_base_url'] + '/v5/market/tickers'
    
    params = {
        'category': 'spot',
        'symbol': symbol
    }
    
    logger.info(f"Fetching ticker for {symbol}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if data.get('retCode') == 0:
                    result = data.get('result', {})
                    tickers = result.get('list', [])
                    
                    if tickers:
                        ticker = tickers[0]
                        return {
                            'symbol': ticker.get('symbol'),
                            'lastPrice': ticker.get('lastPrice'),
                            'bid': ticker.get('bid1Price'),
                            'ask': ticker.get('ask1Price'),
                            'volume': ticker.get('volume24h')
                        }
                    else:
                        logger.error(f"No ticker data for {symbol}")
                        return None
                else:
                    error_msg = data.get('retMsg', 'Unknown error')
                    logger.error(f"Bybit API error: {error_msg}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching ticker: {str(e)}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def get_historical_data(symbol, interval='60', limit=200):
    """
    Fetch historical OHLCV data from Bybit
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        interval: Candle interval in minutes (1, 3, 5, 15, 30, 60, etc.)
        limit: Number of candles to fetch (max 200)
    
    Returns:
        list of OHLCV data
    """
    url = CONFIG['bybit_base_url'] + '/v5/market/kline'
    
    params = {
        'category': 'spot',
        'symbol': symbol,
        'interval': interval,
        'limit': min(limit, 200)
    }
    
    logger.info(f"Fetching historical data for {symbol}, interval={interval}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                if data.get('retCode') == 0:
                    result = data.get('result', {})
                    klines = result.get('list', [])
                    
                    # Parse klines to OHLCV format
                    # Bybit format: [startTime, open, high, low, close, volume, turnover]
                    ohlcv = []
                    for kline in klines:
                        ohlcv.append({
                            'timestamp': int(kline[0]),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                    
                    logger.info(f"Fetched {len(ohlcv)} candles")
                    return ohlcv
                else:
                    error_msg = data.get('retMsg', 'Unknown error')
                    logger.error(f"Bybit API error: {error_msg}")
                    return []
                    
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return []


async def place_order(symbol, side, order_type, qty, price=None):
    """
    Place an order on Bybit
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        side: 'Buy' or 'Sell'
        order_type: 'Market' or 'Limit'
        qty: Order quantity
        price: Limit price (required for limit orders)
    
    Returns:
        dict with order result
    """
    url = CONFIG['bybit_base_url'] + '/v5/order/create'
    timestamp = str(int(time.time() * 1000))
    
    params = {
        'api_key': CONFIG['api_key'],
        'timestamp': timestamp,
        'category': 'spot',
        'symbol': symbol,
        'side': side,
        'orderType': order_type,
        'qty': str(qty)
    }
    
    if order_type == 'Limit' and price:
        params['price'] = str(price)
    
    # Generate signature
    params['sign'] = get_signature(params, CONFIG['api_secret'])
    
    headers = {
        'X-BAPI-API-KEY': CONFIG['api_key'],
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-SIGN': params['sign'],
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Placing {side} {order_type} order: {qty} {symbol} @ {price if price else 'market'}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params, headers=headers) as response:
                data = await response.json()
                
                if data.get('retCode') == 0:
                    logger.info(f"Order placed successfully: {data.get('result')}")
                    return data.get('result')
                else:
                    error_msg = data.get('retMsg', 'Unknown error')
                    logger.error(f"Order failed: {error_msg}")
                    return {'error': error_msg}
                    
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {'error': str(e)}

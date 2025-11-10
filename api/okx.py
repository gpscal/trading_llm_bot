"""
OKX API Integration
Handles all OKX API calls with simple HMAC authentication
Much simpler than Coinbase/Kraken!
"""

import time
import hmac
import hashlib
import base64
import json
import aiohttp
from config.config import CONFIG
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.logger import setup_logger

logger = setup_logger('okx_api_logger', 'okx_api.log')


def get_signature(timestamp, method, request_path, body, secret):
    """
    Generate HMAC SHA256 signature for OKX API
    Simple and straightforward!
    """
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    message = timestamp + method + request_path + body_str
    
    mac = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    
    return base64.b64encode(mac.digest()).decode()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_balance():
    """
    Fetch account balance from OKX
    Returns dict with coin balances
    """
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    method = 'GET'
    request_path = '/api/v5/account/balance'
    
    signature = get_signature(timestamp, method, request_path, '', CONFIG['api_secret'])
    
    url = CONFIG['okx_base_url'] + request_path
    
    headers = {
        'OK-ACCESS-KEY': CONFIG['api_key'],
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': CONFIG['api_passphrase'],
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching balance from OKX")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Response Status: {response.status}")
                logger.info(f"Response: {response_text}")
                
                if response.status == 200:
                    data = json.loads(response_text)
                    
                    if data.get('code') == '0':
                        # Success!
                        balances = {}
                        account_data = data.get('data', [])
                        
                        if account_data:
                            details = account_data[0].get('details', [])
                            for detail in details:
                                currency = detail.get('ccy')
                                available = float(detail.get('availBal', 0))
                                
                                if available > 0:
                                    balances[currency] = available
                        
                        logger.info(f"✅ Balances: {balances}")
                        return balances
                    else:
                        error_msg = data.get('msg', 'Unknown error')
                        logger.error(f"OKX API error: {error_msg}")
                        return {'error': [f'OKX error: {error_msg}']}
                else:
                    logger.error(f"HTTP error {response.status}: {response_text}")
                    return {'error': [f'HTTP {response.status}: {response_text}']}
                    
    except Exception as e:
        logger.error(f"Exception fetching balance: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'error': [str(e)]}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_ticker(symbol):
    """
    Fetch current ticker price from OKX
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USDT')
    
    Returns:
        dict with 'last' price
    """
    # Public endpoint - no authentication needed!
    url = CONFIG['okx_base_url'] + f'/api/v5/market/ticker?instId={symbol}'
    
    logger.info(f"Fetching ticker for {symbol}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == '0':
                        ticker_data = data.get('data', [])
                        if ticker_data:
                            price = float(ticker_data[0].get('last', 0))
                            logger.info(f"Ticker price for {symbol}: {price}")
                            return {'last': price}
                    
                    logger.error(f"OKX ticker error: {data}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status}: {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching ticker: {str(e)}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def get_historical_data(symbol, interval='1H', limit=100):
    """
    Fetch historical OHLCV data from OKX
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USDT')
        interval: Bar size (1m, 5m, 15m, 1H, 4H, 1D)
        limit: Number of bars to fetch (max 300)
    
    Returns:
        list of OHLCV data in Kraken format for compatibility
    """
    # Map our intervals to OKX format
    interval_map = {
        '1': '1m',
        '5': '5m',
        '15': '15m',
        '60': '1H',
        '1440': '1D'
    }
    
    bar = interval_map.get(interval, '1H')
    
    # Public endpoint - no auth needed
    url = CONFIG['okx_base_url'] + f'/api/v5/market/candles?instId={symbol}&bar={bar}&limit={limit}'
    
    logger.info(f"Fetching historical data for {symbol}, bar={bar}, limit={limit}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == '0':
                        candles = data.get('data', [])
                        
                        # Convert to Kraken-like format [time, open, high, low, close, volume]
                        ohlc_data = []
                        for candle in reversed(candles):  # OKX returns newest first
                            ohlc_data.append([
                                int(candle[0]) // 1000,  # timestamp (convert ms to seconds)
                                candle[1],  # open
                                candle[2],  # high
                                candle[3],  # low
                                candle[4],  # close
                                candle[5],  # volume
                            ])
                        
                        logger.info(f"Fetched {len(ohlc_data)} candles")
                        return ohlc_data
                    else:
                        logger.error(f"OKX historical data error: {data}")
                        return []
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status}: {error_text}")
                    return []
                    
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return []


async def place_order(symbol, side, order_type, size, price=None):
    """
    Place an order on OKX
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USDT')
        side: 'buy' or 'sell'
        order_type: 'market' or 'limit'
        size: Order size in base currency
        price: Limit price (required for limit orders)
    
    Returns:
        dict with order result
    """
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    method = 'POST'
    request_path = '/api/v5/trade/order'
    
    # Build order request
    order_data = {
        'instId': symbol,
        'tdMode': 'cash',  # Cash trading (spot)
        'side': side.lower(),
        'ordType': order_type.lower(),
        'sz': str(size)
    }
    
    if order_type.lower() == 'limit' and price:
        order_data['px'] = str(price)
    
    body = json.dumps(order_data)
    signature = get_signature(timestamp, method, request_path, body, CONFIG['api_secret'])
    
    url = CONFIG['okx_base_url'] + request_path
    
    headers = {
        'OK-ACCESS-KEY': CONFIG['api_key'],
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': CONFIG['api_passphrase'],
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Placing {side} {order_type} order: {size} {symbol} @ {price if price else 'market'}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                response_text = await response.text()
                logger.info(f"Order response: {response_text}")
                
                if response.status == 200:
                    data = json.loads(response_text)
                    
                    if data.get('code') == '0':
                        order_info = data.get('data', [{}])[0]
                        logger.info(f"✅ Order placed successfully: {order_info.get('ordId')}")
                        return {
                            'success': True,
                            'order_id': order_info.get('ordId'),
                            'data': order_info
                        }
                    else:
                        error_msg = data.get('msg', 'Unknown error')
                        logger.error(f"Order failed: {error_msg}")
                        return {
                            'success': False,
                            'error': error_msg
                        }
                else:
                    logger.error(f"HTTP error {response.status}: {response_text}")
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}'
                    }
                    
    except Exception as e:
        logger.error(f"Exception placing order: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

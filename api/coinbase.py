"""
Coinbase Advanced API Integration
Handles all Coinbase Advanced Trade API calls with JWT authentication
"""

import time
import jwt
import json
import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from config.config import CONFIG
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.logger import setup_logger

logger = setup_logger('coinbase_api_logger', 'coinbase_api.log')


def build_jwt(api_key, api_secret, uri):
    """
    Build JWT token for Coinbase Advanced API authentication
    """
    # Fix escaped newlines in the private key
    if '\\n' in api_secret:
        api_secret = api_secret.replace('\\n', '\n')
    
    # Load the private key
    try:
        private_key = serialization.load_pem_private_key(
            api_secret.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        logger.info(f"✅ Successfully loaded private key")
    except Exception as e:
        logger.error(f"Failed to load private key: {e}")
        raise ValueError(f"Invalid API secret format: {e}")
    
    # Extract just the API key name from the full path
    # Format: organizations/xxx/apiKeys/yyy -> we need just yyy
    api_key_name = api_key.split('/')[-1] if '/' in api_key else api_key
    
    logger.info(f"API Key (full): {api_key}")
    logger.info(f"API Key (name): {api_key_name}")
    logger.info(f"URI: {uri}")
    
    # Build JWT - trying multiple payload variations
    timestamp = int(time.time())
    
    # Try the exact format from Coinbase Cloud docs
    jwt_payload = {
        'sub': api_key,  # Full API key path
        'iss': 'coinbase-cloud',
        'nbf': timestamp,
        'exp': timestamp + 120,  # 2 minutes
        'aud': ['retail_rest_api_proxy'],
    }
    
    # Some APIs want the URI in payload, some don't - trying WITHOUT first
    logger.info(f"JWT Payload (without URI): {jwt_payload}")
    
    try:
        # Try with full API key in kid header
        jwt_token = jwt.encode(
            jwt_payload,
            private_key,
            algorithm='ES256',
            headers={'kid': api_key, 'nonce': str(timestamp)}  # Try full key path
        )
        logger.info(f"✅ Successfully generated JWT token")
        logger.info(f"JWT Token (first 50 chars): {jwt_token[:50] if isinstance(jwt_token, str) else str(jwt_token)[:50]}")
        return jwt_token
    except Exception as e:
        logger.error(f"Failed to generate JWT: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_balance():
    """
    Fetch account balance from Coinbase Advanced
    Returns dict with coin balances
    """
    uri = 'GET /api/v3/brokerage/accounts'
    jwt_token = build_jwt(CONFIG['api_key'], CONFIG['api_secret'], uri)
    
    url = CONFIG['coinbase_base_url'] + '/api/v3/brokerage/accounts'
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching balance from Coinbase")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Response Status: {response.status}")
                logger.info(f"Response: {response_text}")
                
                if response.status == 200:
                    data = await response.json()
                    accounts = data.get('accounts', [])
                    
                    # Parse balances
                    balances = {}
                    for account in accounts:
                        currency = account.get('currency')
                        available = float(account.get('available_balance', {}).get('value', 0))
                        
                        if available > 0:
                            balances[currency] = available
                    
                    logger.info(f"Balances: {balances}")
                    return balances
                else:
                    # Log more details about the error
                    error_text = await response.text()
                    error_headers = dict(response.headers)
                    logger.error(f"Coinbase API error {response.status}")
                    logger.error(f"Error body: {error_text}")
                    logger.error(f"Error headers: {error_headers}")
                    logger.error(f"Request URL: {url}")
                    logger.error(f"Request headers (no token): {{'Content-Type': headers['Content-Type']}}")
                    
                    # Try to parse error JSON
                    try:
                        error_json = json.loads(error_text)
                        error_message = error_json.get('message', error_text)
                    except:
                        error_message = error_text
                    
                    return {'error': [f'HTTP {response.status}: {error_message}']}
                    
    except Exception as e:
        logger.error(f"Exception fetching balance: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'error': [str(e)]}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_ticker(symbol):
    """
    Fetch current ticker price for a symbol
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USD', 'SOL-USD')
    
    Returns:
        dict with ticker data compatible with Kraken format
    """
    # Coinbase uses product_id like 'BTC-USD'
    product_id = symbol
    url = CONFIG['coinbase_base_url'] + f'/api/v3/brokerage/products/{product_id}/ticker'
    
    logger.info(f"Fetching ticker for {product_id}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    ticker = data.get('trades', [{}])[0] if data.get('trades') else {}
                    
                    # Get the product details for current price
                    product_url = CONFIG['coinbase_base_url'] + f'/api/v3/brokerage/products/{product_id}'
                    async with session.get(product_url) as prod_response:
                        if prod_response.status == 200:
                            product_data = await prod_response.json()
                            price = product_data.get('price', '0')
                            
                            # Return in Kraken-compatible format
                            return {
                                'c': [price, '0'],  # last trade price
                                'a': [price, '0'],  # ask
                                'b': [price, '0'],  # bid
                                'v': ['0', '0'],    # volume
                                'p': [price, price] # volume weighted average price
                            }
                else:
                    logger.error(f"Failed to fetch ticker for {product_id}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching ticker: {str(e)}")
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def get_historical_data(symbol, interval='60', limit=200):
    """
    Fetch historical OHLCV data from Coinbase
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        interval: Candle interval (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, etc.)
        limit: Number of candles to fetch
    
    Returns:
        list of OHLCV data in Kraken format
    """
    # Map interval to Coinbase granularity
    interval_map = {
        '1': 'ONE_MINUTE',
        '5': 'FIVE_MINUTE',
        '15': 'FIFTEEN_MINUTE',
        '60': 'ONE_HOUR',
        '1440': 'ONE_DAY'
    }
    
    granularity = interval_map.get(interval, 'ONE_HOUR')
    product_id = symbol
    
    # Calculate time range (limit * interval in seconds)
    end_time = int(time.time())
    interval_seconds = int(interval) * 60
    start_time = end_time - (limit * interval_seconds)
    
    # Build JWT for this request
    uri = f'GET /api/v3/brokerage/products/{product_id}/candles'
    jwt_token = build_jwt(CONFIG['api_key'], CONFIG['api_secret'], uri)
    
    url = CONFIG['coinbase_base_url'] + f'/api/v3/brokerage/products/{product_id}/candles'
    params = {
        'start': str(start_time),
        'end': str(end_time),
        'granularity': granularity
    }
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Fetching historical data for {product_id}, granularity={granularity}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    candles = data.get('candles', [])
                    
                    # Convert to Kraken OHLC format
                    # Coinbase format: [timestamp, low, high, open, close, volume]
                    ohlcv = []
                    for candle in reversed(candles):  # Reverse to get oldest first
                        ohlcv.append([
                            int(candle['start']),  # timestamp
                            candle['open'],        # open
                            candle['high'],        # high
                            candle['low'],         # low
                            candle['close'],       # close
                            candle['volume'],      # volume
                            '0',                   # vwap (not provided)
                            '0'                    # count (not provided)
                        ])
                    
                    logger.info(f"Fetched {len(ohlcv)} candles")
                    return {product_id.replace('-', ''): ohlcv}
                else:
                    error_text = await response.text()
                    logger.error(f"Error fetching historical data: {error_text}")
                    return {}
                    
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return {}


async def place_order(symbol, side, order_type, size, price=None):
    """
    Place an order on Coinbase Advanced
    
    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        side: 'BUY' or 'SELL'
        order_type: 'MARKET' or 'LIMIT'
        size: Order size (in base currency)
        price: Limit price (required for limit orders)
    
    Returns:
        dict with order result
    """
    order_config = {
        'product_id': symbol,
        'side': side,
        'client_order_id': f'bot_{int(time.time() * 1000)}'
    }
    
    if order_type == 'MARKET':
        if side == 'BUY':
            # For market buy, specify quote currency (USD) amount
            order_config['order_configuration'] = {
                'market_market_ioc': {
                    'quote_size': str(size)
                }
            }
        else:
            # For market sell, specify base currency amount
            order_config['order_configuration'] = {
                'market_market_ioc': {
                    'base_size': str(size)
                }
            }
    else:  # LIMIT
        order_config['order_configuration'] = {
            'limit_limit_gtc': {
                'base_size': str(size),
                'limit_price': str(price),
                'post_only': False
            }
        }
    
    # Build JWT for this request
    uri = 'POST /api/v3/brokerage/orders'
    jwt_token = build_jwt(CONFIG['api_key'], CONFIG['api_secret'], uri)
    
    url = CONFIG['coinbase_base_url'] + '/api/v3/brokerage/orders'
    body = json.dumps(order_config)
    
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
    
    logger.info(f"Placing {side} {order_type} order: {size} {symbol} @ {price if price else 'market'}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"Order placed successfully: {data}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Order failed: {error_text}")
                    return {'error': error_text}
                    
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        return {'error': str(e)}

import time
import hmac
import hashlib
import base64
import aiohttp
import asyncio
import socket
from urllib.parse import urlencode
from config.config import CONFIG
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.logger import setup_logger

logger = setup_logger('kraken_api_logger', 'kraken_api.log')


def create_aiohttp_connector():
    """
    Create aiohttp connector with proper DNS and timeout settings.
    
    - Forces IPv4 for more reliable DNS resolution
    - Caches DNS results to avoid repeated lookups
    - Configures connection pooling
    """
    return aiohttp.TCPConnector(
        family=socket.AF_INET,      # Force IPv4 for more reliable DNS
        ttl_dns_cache=300,           # Cache DNS for 5 minutes
        use_dns_cache=True,          # Enable DNS caching
        limit=10,                    # Connection pool limit
        limit_per_host=5,            # Connections per host
        enable_cleanup_closed=True,  # Clean up closed connections
        force_close=False,           # Reuse connections
        ssl=None                     # Use default SSL context
    )


def create_client_timeout():
    """
    Create timeout configuration for aiohttp.
    
    Longer timeouts to handle slow DNS resolution and network issues.
    """
    return aiohttp.ClientTimeout(
        total=30,          # Total timeout (30 seconds)
        connect=10,        # Connection timeout (10 seconds)
        sock_read=20,      # Socket read timeout (20 seconds)
        sock_connect=10    # Socket connect timeout (10 seconds)
    )

def get_signature(url_path, data, secret):
    postdata = urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = url_path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sig_digest = base64.b64encode(mac.digest())
    return sig_digest.decode()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_balance():
    url_path = '/0/private/Balance'
    url = CONFIG['base_url'] + url_path
    nonce = str(int(time.time() * 1000))
    data = {'nonce': nonce}
    headers = {
        'API-Key': CONFIG['api_key'],
        'API-Sign': get_signature(url_path, data, CONFIG['api_secret'])
    }

    logger.info(f"URL: {url}")
    logger.info(f"Data: {data}")
    logger.info(f"Headers: {headers}")

    connector = create_aiohttp_connector()
    timeout = create_client_timeout()

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(url, headers=headers, data=data) as response:
                # Read response once as JSON
                response_json = await response.json()
                logger.info(f"Response: {response_json}")
                
                # Check for errors in Kraken response
                if 'error' in response_json and response_json['error']:
                    error_list = response_json['error']
                    logger.error(f"Kraken API error: {error_list}")
                    return {'error': error_list}
                
                # Return result if successful
                if 'result' in response_json:
                    logger.info(f"✅ Balance fetched successfully")
                    return response_json['result']
                else:
                    logger.error(f"Unexpected response structure: {response_json}")
                    return {'error': ['Unexpected response format']}
                    
    except Exception as e:
        logger.error(f"Exception fetching balance: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'error': [str(e)]}

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_historical_data(pair, interval):
    """
    Fetch historical OHLCV data from Kraken API with rate limit handling.
    
    Implements exponential backoff for rate limit errors.
    """
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    
    connector = create_aiohttp_connector()
    timeout = create_client_timeout()
    max_retries = 3
    base_delay = 5  # Start with 5 seconds
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # Check for rate limiting error
                    if 'error' in data and data['error']:
                        error_msg = data['error']
                        if any('Too many requests' in str(err) or 'rate limit' in str(err).lower() for err in error_msg):
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                                logger.warning(f"Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                                await asyncio.sleep(delay)
                                continue
                            else:
                                logger.error(f"Rate limited after {max_retries} attempts: {error_msg}")
                                return None
                        else:
                            logger.error(f"Error fetching historical data: {error_msg}")
                            return None
                    
                    response.raise_for_status()
                    
                    # Success
                    result = data['result'].get(pair)
                    if result:
                        logger.debug(f"Successfully fetched {len(result)} candles for {pair}")
                    return result
                    
        except aiohttp.ClientError as e:
            logger.error(f"Client error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
            else:
                return None
        except aiohttp.ServerError as e:
            logger.error(f"Server error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
            else:
                return None
        except Exception as e:
            logger.error(f"Unexpected error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
            else:
                return None
    
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_ticker(pair):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    connector = create_aiohttp_connector()
    timeout = create_client_timeout()
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async with session.get(url) as response:
            try:
                data = await response.json()
                response.raise_for_status()
                if 'error' in data and data['error']:
                    logger.error(f"Error fetching ticker for {pair}: {data['error']}")
                    return None
                return data['result'].get(pair)
            except aiohttp.ClientError as e:
                logger.error(f"Client error fetching ticker for {pair}: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching ticker for {pair}: {str(e)}")
                return None

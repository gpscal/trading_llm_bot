import time
import hmac
import hashlib
import base64
import aiohttp
from urllib.parse import urlencode
from config.config import CONFIG
from tenacity import retry, stop_after_attempt, wait_fixed
from utils.logger import setup_logger

logger = setup_logger('kraken_api_logger', 'kraken_api.log')

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

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=urlencode(data)) as response:
                response_text = await response.text()
                logger.info(f"Response text: {response_text}")
                response.raise_for_status()
                data = await response.json()
                if 'result' in data:
                    return data['result']
                else:
                    logger.error(f"Unexpected response structure: {data}")
                    return {'error': data.get('error', ['Unknown error'])}
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        return {'error': [str(e)]}

async def get_historical_data(pair, interval):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data['error']:
                print(f"Error fetching historical data: {data['error']}")
                return None
            return data['result'][pair]

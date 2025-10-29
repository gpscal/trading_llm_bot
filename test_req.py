import aiohttp
import asyncio
import hashlib
import hmac
import base64
import time
import os
from dotenv import load_dotenv
from config.config import CONFIG
import urllib.parse

# Load environment variables from .env file
load_dotenv()

api_key = CONFIG['api_key'];
api_secret = CONFIG['api_secret'];

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode('utf-8')
    message = urlpath.encode('utf-8') + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

async def get_historical_data(pair, interval):
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data['error']:
                print(f"Error fetching historical data: {data['error']}")
                return None
            return data['result'][pair]

async def get_balance():
    url = "https://api.kraken.com/0/private/Balance"
    nonce = str(int(time.time() * 1000))
    data = {
        'nonce': nonce
    }
    headers = {
        'API-Key': api_key,
        'API-Sign': get_kraken_signature('/0/private/Balance', data, api_secret)
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            data = await response.json()
            if data['error']:
                print(f"Error fetching balance: {data['error']}")
                return None
            return data['result']

async def test_request():
    pair = 'XXBTZUSD'  # Example pair
    interval = 60  # Example interval
    data = await get_historical_data(pair, interval)
    if data:
        print("Historical data fetched successfully:")
        print(data)
    else:
        print("Failed to fetch historical data.")

    balance = await get_balance()
    if balance:
        print("Balance fetched successfully:")
        print(balance)
    else:
        print("Failed to fetch balance.")

if __name__ == "__main__":
    asyncio.run(test_request())
    asyncio.run(test_request())
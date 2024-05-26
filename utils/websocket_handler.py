import numpy as np
from colorama import Fore, Style
from utils.utils import get_timestamp, log_and_print_status
from strategies.indicators import calculate_indicators
from api.kraken import get_historical_data
from trade.trade_logic import handle_trade_with_fees
from config.config import CONFIG
import asyncio
import logging

# Set up logger
logger = logging.getLogger('websocket_handler_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('websocket_handler.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def handle_websocket_data(message, balance):
    if isinstance(message, dict) and 'event' in message:
        if message['event'] == 'subscriptionStatus' and message['status'] == 'subscribed':
            logger.info(f"Subscribed to {message['pair']}")
        elif message['event'] == 'systemStatus':
            logger.info(f"System status: {message['status']}")
    elif isinstance(message, list) and len(message) == 4:
        channel_id, data, event_type, pair = message
        if event_type == 'ticker':
            if pair == 'XBT/USD':
                btc_price = float(data['c'][0])
                balance['btc_price'] = btc_price
                balance['btc_indicators'] = {
                    'moving_avg': np.mean([float(data['v'][0]), float(data['v'][1])]),
                    'bollinger_bands': (max(float(data['h'][0]), float(data['h'][1])), min(float(data['l'][0]), float(data['l'][1]))),
                    'macd': (float(data['p'][0]), float(data['p'][1])),
                    'rsi': 50,
                    'atr': np.array([float(data['h'][0]) - float(data['l'][0]), float(data['h'][1]) - float(data['l'][1])]),
                    'correlation': 0.9,
                    'stochastic_oscillator': 30,
                    'momentum': -2000
                }
                logger.info(f"BTC price updated: {btc_price}")
            elif pair == 'SOL/USD':
                sol_price = float(data['c'][0])
                balance['sol_price'] = sol_price
                balance['sol_indicators'] = {
                    'moving_avg': np.mean([float(data['v'][0]), float(data['v'][1])]),
                    'bollinger_bands': (max(float(data['h'][0]), float(data['h'][1])), min(float(data['l'][0]), float(data['l'][1]))),
                    'macd': (float(data['p'][0]), float(data['p'][1])),
                    'rsi': 50,
                    'atr': np.array([float(data['h'][0]) - float(data['l'][0]), float(data['h'][1]) - float(data['l'][1])]),
                    'correlation': 0.9,
                    'stochastic_oscillator': 30,
                    'momentum': -2000
                }
                logger.info(f"SOL price updated: {sol_price}")

async def start_websocket(url, pairs, on_data, balance):
    print(f"Connecting to websocket at {url}...")
    logger.info(f"Connecting to websocket at {url}...")
    try:
        async with websockets.connect(url) as ws:
            print(f"Connected to websocket at {url}. Subscribing to pairs {pairs}...")
            logger.info(f"Connected to websocket at {url}. Subscribing to pairs {pairs}...")

            subscribe_message = json.dumps({
                "event": "subscribe",
                "pair": pairs,
                "subscription": {"name": "ticker"}
            })
            await ws.send(subscribe_message)
            print(f"Sent subscription message: {subscribe_message}")
            logger.info(f"Sent subscription message: {subscribe_message}")

            while True:
                try:
                    data = await ws.recv()
                    message = json.loads(data)
                    await on_data(message, balance)
                except websockets.ConnectionClosed:
                    print(f"[{get_timestamp()}] WebSocket closed, reconnecting...")
                    logger.warning(f"[{get_timestamp()}] WebSocket closed, reconnecting...")
                    await asyncio.sleep(5)
                    await start_websocket(url, pairs, on_data, balance)
                except Exception as e:
                    print(f"Error in WebSocket: {str(e)}")
                    logger.error(f"Error in WebSocket: {str(e)}")
                    await asyncio.sleep(5)
    except Exception as e:
        print(f"Failed to connect to websocket: {e}")
        logger.error(f"Failed to connect to websocket: {e}")

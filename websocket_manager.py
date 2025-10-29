import asyncio
import websockets
import json
from utils.utils import get_timestamp
import logging
from config.config import CONFIG
import random

# Set up logger
logger = logging.getLogger('websocket_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('websocket.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def start_websocket(url, pairs, on_data, balance):
    base_delay = 1
    max_delay = 30
    attempt = 0
    while True:
        delay = min(max_delay, base_delay * (2 ** attempt))
        jitter = random.uniform(0, 1)
        try:
            logger.info(f"Connecting to websocket at {url} (attempt {attempt + 1})...")
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                logger.info(f"Connected to websocket at {url}. Subscribing to pairs {pairs}...")

                subscribe_message = json.dumps({
                    "event": "subscribe",
                    "pair": pairs,
                    "subscription": {"name": "ticker"}
                })
                await ws.send(subscribe_message)
                logger.info(f"Sent subscription message: {subscribe_message}")

                attempt = 0  # reset backoff after successful connect
                while True:
                    try:
                        data = await ws.recv()
                        message = json.loads(data)
                        await on_data(message, balance)
                    except websockets.ConnectionClosed:
                        logger.warning(f"[{get_timestamp()}] WebSocket closed, will reconnect...")
                        break
                    except Exception as e:
                        logger.error(f"Error in WebSocket receive loop: {str(e)}")
                        await asyncio.sleep(2)
                        break
        except Exception as e:
            logger.error(f"Failed to connect to websocket: {e}")
            attempt += 1
        # Backoff before retry
        sleep_for = delay + jitter
        logger.info(f"Reconnecting in {sleep_for:.1f}s (attempt {attempt + 1})")
        await asyncio.sleep(sleep_for)

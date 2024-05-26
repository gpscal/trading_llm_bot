import asyncio
import websockets
import json
from utils.utils import get_timestamp
import logging
from config.config import CONFIG

# Set up logger
logger = logging.getLogger('websocket_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('websocket.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def start_websocket(url, pairs, on_data, balance):
    logger.info(f"Connecting to websocket at {url}...")
    try:
        async with websockets.connect(url) as ws:
            logger.info(f"Connected to websocket at {url}. Subscribing to pairs {pairs}...")

            subscribe_message = json.dumps({
                "event": "subscribe",
                "pair": pairs,
                "subscription": {"name": "ticker"}
            })
            await ws.send(subscribe_message)
            logger.info(f"Sent subscription message: {subscribe_message}")

            while True:
                try:
                    data = await ws.recv()
                    message = json.loads(data)
                    await on_data(message, balance)
                except websockets.ConnectionClosed:
                    logger.warning(f"[{get_timestamp()}] WebSocket closed, reconnecting...")
                    await asyncio.sleep(5)
                    await start_websocket(url, pairs, on_data, balance)
                except Exception as e:
                    logger.error(f"Error in WebSocket: {str(e)}")
                    await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Failed to connect to websocket: {e}")

import asyncio
import json
import logging

import websockets

from utils.utils import get_timestamp

# Set up logger
logger = logging.getLogger('websocket_handler_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('websocket_handler.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

def _update_price(balance: dict, asset: str, price: float) -> None:
    """Update balance pricing info while keeping previously calculated indicators intact."""
    asset_upper = asset.upper()
    
    # Update legacy price keys
    price_key = f"{asset}_price"
    previous_price = balance.get(price_key)
    balance[price_key] = price
    
    # Update multi-coin structure
    if 'coins' in balance and asset_upper in balance['coins']:
        coin_state = balance['coins'][asset_upper]
        previous_price = coin_state.get('price', previous_price)
        coin_state['price'] = price
        
        # Update indicators with new price
        indicators = coin_state.get('indicators', {})
        if isinstance(indicators, dict):
            indicators['last_price'] = price
            if previous_price is not None:
                # Simple momentum approximation using price delta
                indicators['momentum'] = price - previous_price
    
    # Update legacy indicators
    indicators_key = f"{asset}_indicators"
    indicators = balance.get(indicators_key)
    if isinstance(indicators, dict):
        indicators['last_price'] = price
        if previous_price is not None:
            indicators['momentum'] = price - previous_price


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
                _update_price(balance, 'btc', btc_price)
                logger.debug(f"BTC price updated to {btc_price}")
            elif pair == 'SOL/USD':
                sol_price = float(data['c'][0])
                _update_price(balance, 'sol', sol_price)
                logger.debug(f"SOL price updated to {sol_price}")

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

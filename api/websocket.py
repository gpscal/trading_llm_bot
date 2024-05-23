import asyncio
import websockets
import json
from utils.utils import get_timestamp

async def start_websocket(url, pairs, on_data):
    async with websockets.connect(url) as ws:
        subscribe_message = json.dumps({
            "event": "subscribe",
            "pair": pairs,
            "subscription": {"name": "ticker"}
        })
        await ws.send(subscribe_message)

        while True:
            try:
                data = await ws.recv()
                message = json.loads(data)
                await on_data(message)
            except websockets.ConnectionClosed:
                print(f"[{get_timestamp()}] WebSocket closed, reconnecting...")
                await asyncio.sleep(5)
                await start_websocket(url, pairs, on_data)
            except Exception as e:
                print(f"Error in WebSocket: {str(e)}")

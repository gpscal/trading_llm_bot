import asyncio
import aiohttp
from config.config import CONFIG

async def _post_json(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=10) as resp:
            await resp.text()

def notify(text: str):
    """Legacy notification function - no longer used. Discord notifications are handled by discord_notifier.py"""
    pass



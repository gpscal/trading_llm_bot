import asyncio
import aiohttp
from config.config import CONFIG

async def _post_json(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=10) as resp:
            await resp.text()

async def send_slack_message_async(text: str):
    webhook = CONFIG.get('slack_webhook_url')
    if not CONFIG.get('alerts_enabled') or not webhook:
        return
    payload = {"text": text}
    try:
        await _post_json(webhook, payload)
    except Exception:
        pass

async def send_telegram_message_async(text: str):
    if not CONFIG.get('alerts_enabled'):
        return
    token = CONFIG.get('telegram_bot_token')
    chat_id = CONFIG.get('telegram_chat_id')
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        await _post_json(url, payload)
    except Exception:
        pass

def notify(text: str):
    """Fire-and-forget notifications to Slack and Telegram."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule without awaiting
            asyncio.create_task(send_slack_message_async(text))
            asyncio.create_task(send_telegram_message_async(text))
        else:
            loop.run_until_complete(send_slack_message_async(text))
            loop.run_until_complete(send_telegram_message_async(text))
    except RuntimeError:
        # No running loop
        asyncio.run(send_slack_message_async(text))
        asyncio.run(send_telegram_message_async(text))



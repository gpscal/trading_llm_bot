import asyncio
from api.websocket import start_websocket
from utils.websocket_handler import handle_websocket_data
from utils.periodic_tasks import print_status_periodically
from config.config import CONFIG
from colorama import Fore, Style, init
import aiohttp

# Initialize colorama
init(autoreset=True)

async def fetch_initial_sol_price():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.kraken.com/0/public/Ticker?pair=SOLUSD") as response:
            data = await response.json()
            return float(data['result']['SOLUSD']['c'][0])

async def main():
    sol_initial_price = await fetch_initial_sol_price()
    balance = {
        'usdt': CONFIG['initial_balance_usdt'],
        'sol': CONFIG['initial_balance_sol'],
        'sol_price': sol_initial_price
    }
    balance['initial_total_usd'] = balance['usdt'] + balance['sol'] * balance['sol_price']
    print(f"{Fore.CYAN}Initial Balance: {balance}{Style.RESET_ALL}")
    await start_websocket(
        url=CONFIG['websocket_url'],
        pairs=['XBT/USD', 'SOL/USD'],
        on_data=handle_websocket_data
    )

    # Periodically print status
    asyncio.create_task(print_status_periodically(balance))

if __name__ == "__main__":
    asyncio.run(main())

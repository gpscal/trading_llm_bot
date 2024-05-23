import asyncio
from api.websocket import start_websocket
from utils.websocket_handler import handle_websocket_data
from utils.periodic_tasks import print_status_periodically
from config.config import CONFIG
from utils.data_fetchers import fetch_initial_sol_price, fetch_and_analyze_historical_data  # Import shared functions
from colorama import Fore, Style, init
import logging

# Initialize colorama
init(autoreset=True)

# Set up logger
logger = logging.getLogger('simulate_logger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('simulate.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

async def main():
    sol_initial_price = await fetch_initial_sol_price()
    balance = {
        'usdt': CONFIG['initial_balance_usdt'],
        'sol': CONFIG['initial_balance_sol'],
        'sol_price': sol_initial_price
    }
    initial_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
    balance['initial_total_usd'] = round(initial_total_usd, 2)
    
    logger.info(f"Initial SOL Price: {sol_initial_price}")
    logger.info(f"Initial Total USD (before rounding): {initial_total_usd}")
    logger.info(f"Initial Total USD (after rounding): {balance['initial_total_usd']}")

    print(f"{Fore.CYAN}Initial Balance: {balance}{Style.RESET_ALL}")

    pairs = {
        'btc': 'XXBTZUSD',
        'sol': 'SOLUSDT'
    }
    
    await fetch_and_analyze_historical_data(pairs, balance)  # Initial fetch and analysis

    await start_websocket(
        url=CONFIG['websocket_url'],
        pairs=['XBT/USD', 'SOL/USD'],
        on_data=handle_websocket_data
    )

    # Periodically print status
    asyncio.create_task(print_status_periodically(balance))

    while True:
        await asyncio.sleep(CONFIG['poll_interval'])  # Poll interval
        await fetch_and_analyze_historical_data(pairs, balance)  # Periodically update historical data and indicators

if __name__ == "__main__":
    asyncio.run(main())

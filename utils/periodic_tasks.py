import asyncio
from colorama import Fore
from utils.utils import get_timestamp, print_status

async def print_status_periodically(balance):
    while True:
        current_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
        total_gain_usd = current_total_usd - balance['initial_total_usd']
        print_status(get_timestamp(), balance['btc_price'], balance['sol_price'], balance['btc_momentum'], balance['confidence'], balance['usdt'], balance['sol'], current_total_usd, total_gain_usd)
        await asyncio.sleep(60)

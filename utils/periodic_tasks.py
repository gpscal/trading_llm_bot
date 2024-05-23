import asyncio
from colorama import Fore
from utils.utils import get_timestamp, print_status

async def print_status_periodically(balance):
    while True:
        current_total_usd_before_rounding = balance['usdt'] + balance['sol'] * balance['sol_price']
        current_total_usd = round(current_total_usd_before_rounding, 2)
        total_gain_usd = round(current_total_usd - balance['initial_total_usd'], 2)
        
        # Logging detailed balance and calculation
        print(f"{Fore.YELLOW}Current USDT: {balance['usdt']}, SOL: {balance['sol']}, SOL Price: {balance['sol_price']}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Current Total USD (before rounding): {current_total_usd_before_rounding}, Total USD (after rounding): {current_total_usd}, Initial Total USD: {balance['initial_total_usd']}, Total Gain USD: {total_gain_usd}{Style.RESET_ALL}")
        
        print_status(get_timestamp(), balance['btc_price'], balance['sol_price'], balance['btc_momentum'], balance['confidence'], balance['usdt'], balance['sol'], current_total_usd, total_gain_usd)
        await asyncio.sleep(60)  # Adjust the interval to control the logging frequency

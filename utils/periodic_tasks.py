import asyncio
from colorama import Fore, Style
from utils.utils import get_timestamp, log_and_print_status

async def print_status_periodically(balance):
    while True:
        try:
            usdt_balance = float(balance.get('usdt', 0.0))
            sol_balance = float(balance.get('sol', 0.0))
            sol_price = float(balance.get('sol_price', 0.0))

            current_total_usd_before_rounding = usdt_balance + sol_balance * sol_price
            current_total_usd = round(current_total_usd_before_rounding, 2)
            initial_total_usd = float(balance.get('initial_total_usd', 0.0))
            total_gain_usd = round(current_total_usd - initial_total_usd, 2)
            
            # Logging detailed balance and calculation
            print(f"{Fore.YELLOW}Current USDT: {usdt_balance}, SOL: {sol_balance}, SOL Price: {sol_price}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Current Total USD (before rounding): {current_total_usd_before_rounding}, Total USD (after rounding): {current_total_usd}, Initial Total USD: {initial_total_usd}, Total Gain USD: {total_gain_usd}{Style.RESET_ALL}")
            
            log_and_print_status(
                balance=balance,
                current_total_usd=current_total_usd,
                total_gain_usd=total_gain_usd
            )
        except ValueError as e:
            print(f"{Fore.RED}Error in print_status_periodically: {e}{Fore.RESET}")
        except TypeError as e:
            print(f"{Fore.RED}Type error in print_status_periodically: {e}{Fore.RESET}")

        await asyncio.sleep(60)  # Adjust the interval to control the logging frequency

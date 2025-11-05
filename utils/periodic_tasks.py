import asyncio
from colorama import Fore, Style
from utils.logger import setup_logger
from utils.utils import calculate_total_usd, calculate_total_gain_usd
from utils.shared_state import append_log_safe

logger = setup_logger('periodic_tasks', 'periodic_tasks.log')

async def print_status_periodically(balance):
    while True:
        current_total_usd = calculate_total_usd(balance)
        total_gain_usd = calculate_total_gain_usd(current_total_usd, balance.get('initial_total_usd', 0))
        
        selected_coin = balance.get('selected_coin', 'SOL')
        coins = balance.get('coins', {})
        
        # Build coin balances summary
        coin_summaries = []
        for coin, data in coins.items():
            amount = data.get('amount', 0.0)
            price = data.get('price', 0.0)
            value = amount * price
            coin_summaries.append(f"{coin}: {amount:.6f} @ ${price:.2f} = ${value:.2f}")
        
        status_message = (
            f"Trading: {selected_coin}\n"
            f"USDT Balance: ${balance.get('usdt', 0.0):.2f}\n"
            f"{chr(10).join(coin_summaries)}\n"
            f"Total Portfolio Value: ${current_total_usd:.2f}\n"
            f"Total Gain: ${total_gain_usd:.2f} ({(total_gain_usd / balance.get('initial_total_usd', 1) * 100):.2f}%)"
        )
        
        print(status_message)
        logger.info(status_message)
        
        # Update shared state
        append_log_safe(status_message)
        
        await asyncio.sleep(60)  # Adjust the interval to control the logging frequency

import asyncio
from colorama import Fore, Style
from utils.logger import setup_logger
from utils.utils import calculate_total_usd, calculate_total_gain_usd
from utils.shared_state import update_bot_state

logger = setup_logger('periodic_tasks', 'periodic_tasks.log')

async def print_status_periodically(balance):
    while True:
        current_total_usd = calculate_total_usd(balance)
        total_gain_usd = calculate_total_gain_usd(current_total_usd, balance['initial_total_usd'])
        
        status_message = (
            f"Current Balances: USDT: {balance['usdt']:.2f}, SOL: {balance['sol']:.2f}\n"
            f"Current SOL Price: {balance['sol_price']:.2f}\n"
            f"Current Total USD: {current_total_usd:.2f}\n"
            f"Total Gain USD: {total_gain_usd:.2f}"
        )
        
        print(status_message)
        logger.info(status_message)
        
        # Update shared state
        update_bot_state({"logs": bot_state['logs'] + [status_message]})
        
        await asyncio.sleep(60)  # Adjust the interval to control the logging frequency

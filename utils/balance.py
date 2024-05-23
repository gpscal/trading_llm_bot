import asyncio
from colorama import Fore
from config.config import CONFIG
from api.kraken import get_balance

async def initialize_balances():
    initial_balance = await get_balance()
    if 'error' in initial_balance:
        print(f"{Fore.RED}Error: {initial_balance['error']}")
        initial_balance = {
            'USDT': CONFIG['initial_balance_usdt'],
            'SOL': CONFIG['initial_balance_sol']
        }
    return {
        'usdt': initial_balance.get('USDT', CONFIG['initial_balance_usdt']),
        'sol': initial_balance.get('SOL', CONFIG['initial_balance_sol'])
    }

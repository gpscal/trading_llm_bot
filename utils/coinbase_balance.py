"""
Coinbase-specific balance initialization
"""

import asyncio
from colorama import Fore
from config.config import CONFIG
from api.coinbase import get_balance

async def initialize_balances():
    """
    Initialize balances from Coinbase account
    Falls back to config values if API fails
    """
    initial_balance = await get_balance()
    
    if 'error' in initial_balance:
        print(f"{Fore.RED}Error connecting to Coinbase: {initial_balance['error']}")
        print(f"{Fore.YELLOW}Falling back to simulation mode with config values")
        initial_balance = {
            'USD': CONFIG['initial_balance_usdt'],
            'SOL': CONFIG['initial_balance_sol'],
            'BTC': CONFIG['initial_balance_btc']
        }
    else:
        print(f"{Fore.GREEN}✅ Successfully connected to Coinbase!")
    
    # Parse Coinbase balance format
    return {
        'usdt': float(initial_balance.get('USD', initial_balance.get('USDT', CONFIG['initial_balance_usdt']))),
        'sol': float(initial_balance.get('SOL', CONFIG['initial_balance_sol'])),
        'btc': float(initial_balance.get('BTC', CONFIG['initial_balance_btc']))
    }

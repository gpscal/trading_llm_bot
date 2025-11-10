"""
Bybit-specific balance initialization
Replaces kraken balance.py for Bybit exchange
"""

import asyncio
from colorama import Fore
from config.config import CONFIG
from api.bybit import get_balance

async def initialize_balances():
    """
    Initialize balances from Bybit account
    Falls back to config values if API fails
    """
    initial_balance = await get_balance()
    
    if 'error' in initial_balance:
        print(f"{Fore.RED}Error connecting to Bybit: {initial_balance['error']}")
        print(f"{Fore.YELLOW}Falling back to simulation mode with config values")
        initial_balance = {
            'USDT': CONFIG['initial_balance_usdt'],
            'SOL': CONFIG['initial_balance_sol'],
            'BTC': CONFIG['initial_balance_btc']
        }
    else:
        print(f"{Fore.GREEN}✅ Successfully connected to Bybit!")
    
    # Parse Bybit balance format
    return {
        'usdt': float(initial_balance.get('USDT', CONFIG['initial_balance_usdt'])),
        'sol': float(initial_balance.get('SOL', CONFIG['initial_balance_sol'])),
        'btc': float(initial_balance.get('BTC', CONFIG['initial_balance_btc']))
    }

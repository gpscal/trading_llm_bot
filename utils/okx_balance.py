"""
OKX Balance Initialization
Handles balance fetching with fallback to simulation mode
"""

import os
from colorama import Fore
from api.okx import get_balance
from config.config import CONFIG


async def initialize_balances():
    """
    Initialize balances from OKX or fall back to simulation mode
    
    Returns:
        dict: Balance dictionary with usdt, sol, btc
    """
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}Initializing OKX Balance...")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    initial_balance = await get_balance()
    
    if 'error' in initial_balance:
        print(f"{Fore.RED}❌ Error connecting to OKX: {initial_balance['error']}")
        print(f"{Fore.YELLOW}⚠️  Falling back to simulation mode with config values")
        print(f"{Fore.YELLOW}    (This means you're NOT trading with real money!){Fore.RESET}")
        
        initial_balance = {
            'USDT': CONFIG['initial_balance_usdt'],
            'SOL': CONFIG['initial_balance_sol'],
            'BTC': CONFIG['initial_balance_btc']
        }
    else:
        print(f"{Fore.GREEN}✅ Successfully connected to OKX!")
        print(f"{Fore.GREEN}📊 Account Balances:{Fore.RESET}")
        for currency, amount in initial_balance.items():
            print(f"{Fore.WHITE}   {currency}: {amount:.6f}{Fore.RESET}")
        print()
    
    # Return in standard format
    return {
        'usdt': float(initial_balance.get('USDT', initial_balance.get('USD', CONFIG['initial_balance_usdt']))),
        'sol': float(initial_balance.get('SOL', CONFIG['initial_balance_sol'])),
        'btc': float(initial_balance.get('BTC', CONFIG['initial_balance_btc']))
    }

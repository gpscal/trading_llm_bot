#!/usr/bin/env python3
"""
Test OKX API Connection
Simple script to verify your OKX API credentials work correctly
"""

import asyncio
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Import OKX API functions
from api.okx import get_balance, get_ticker


async def test_okx_connection():
    """Test OKX API connection and credentials"""
    
    print("="*70)
    print(f"{Fore.CYAN}🔑 Testing OKX API Connection...{Style.RESET_ALL}")
    print("="*70)
    print()
    
    # Test 1: Get Balance (requires authentication)
    print(f"{Fore.YELLOW}Test 1: Fetching account balance...{Style.RESET_ALL}")
    print("-"*70)
    
    try:
        balance = await get_balance()
        
        if 'error' in balance:
            print(f"{Fore.RED}❌ API Connection FAILED{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {balance['error']}{Style.RESET_ALL}")
            print()
            print(f"{Fore.YELLOW}Common issues:{Style.RESET_ALL}")
            print("  1. API Key, Secret, or Passphrase is incorrect")
            print("  2. API key doesn't have 'Trade' permission")
            print("  3. API key is for wrong account type (use Trading account)")
            print("  4. IP whitelist restrictions (disable or add your IP)")
            print()
            print(f"{Fore.CYAN}To fix:{Style.RESET_ALL}")
            print("  1. Go to https://www.okx.com/account/my-api")
            print("  2. Create new API key with 'Trade' permission")
            print("  3. Copy API Key, Secret, AND Passphrase to .env file")
            print("  4. Make sure IP whitelist is disabled (or add your IP)")
            print()
            return False
        else:
            print(f"{Fore.GREEN}✅ API Connection SUCCESSFUL!{Style.RESET_ALL}")
            print()
            print(f"{Fore.CYAN}Your OKX Account Balances:{Style.RESET_ALL}")
            
            if balance:
                for currency, amount in balance.items():
                    print(f"  {Fore.WHITE}{currency}: {amount:.6f}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.YELLOW}(Empty account - deposit funds to start trading){Style.RESET_ALL}")
            
            print()
    
    except Exception as e:
        print(f"{Fore.RED}❌ Exception during balance fetch: {e}{Style.RESET_ALL}")
        return False
    
    # Test 2: Get Ticker (public endpoint, no auth needed)
    print(f"{Fore.YELLOW}Test 2: Fetching BTC-USDT ticker...{Style.RESET_ALL}")
    print("-"*70)
    
    try:
        ticker = await get_ticker('BTC-USDT')
        
        if ticker and 'last' in ticker:
            price = ticker['last']
            print(f"{Fore.GREEN}✅ Ticker fetch SUCCESSFUL!{Style.RESET_ALL}")
            print(f"  {Fore.WHITE}BTC-USDT Price: ${price:,.2f}{Style.RESET_ALL}")
            print()
        else:
            print(f"{Fore.RED}❌ Failed to fetch ticker{Style.RESET_ALL}")
            return False
    
    except Exception as e:
        print(f"{Fore.RED}❌ Exception during ticker fetch: {e}{Style.RESET_ALL}")
        return False
    
    # Test 3: Get Ticker for SOL
    print(f"{Fore.YELLOW}Test 3: Fetching SOL-USDT ticker...{Style.RESET_ALL}")
    print("-"*70)
    
    try:
        ticker = await get_ticker('SOL-USDT')
        
        if ticker and 'last' in ticker:
            price = ticker['last']
            print(f"{Fore.GREEN}✅ Ticker fetch SUCCESSFUL!{Style.RESET_ALL}")
            print(f"  {Fore.WHITE}SOL-USDT Price: ${price:,.2f}{Style.RESET_ALL}")
            print()
        else:
            print(f"{Fore.RED}❌ Failed to fetch ticker{Style.RESET_ALL}")
            return False
    
    except Exception as e:
        print(f"{Fore.RED}❌ Exception during ticker fetch: {e}{Style.RESET_ALL}")
        return False
    
    # All tests passed!
    print("="*70)
    print(f"{Fore.GREEN}🎉 ALL TESTS PASSED!{Style.RESET_ALL}")
    print("="*70)
    print()
    print(f"{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
    print("  1. ✅ Your OKX API is working correctly!")
    print("  2. 💰 Make sure you have USDT in your account to trade")
    print("  3. 🚀 Start trading: python3 live_trade.py")
    print()
    print(f"{Fore.YELLOW}Note: Start in simulation mode first to test your strategy!{Style.RESET_ALL}")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_okx_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

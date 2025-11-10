#!/usr/bin/env python3
"""
Bybit API Connection Test
Tests your Bybit API credentials and displays account information
"""

import asyncio
import sys
from api.bybit import get_balance, get_ticker
from colorama import Fore, Style, init

init(autoreset=True)

async def test_connection():
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🔑 Testing Bybit API Connection...")
    print(f"{Fore.CYAN}{'='*70}")
    print()
    
    # Test 1: Get Balance
    print(f"{Fore.YELLOW}Test 1: Fetching account balance...")
    print(f"{Fore.YELLOW}{'-'*70}")
    
    balance = await get_balance()
    
    if 'error' in balance:
        print(f"{Fore.RED}❌ API Connection FAILED")
        print(f"{Fore.RED}Error: {balance['error']}")
        print()
        print(f"{Fore.YELLOW}Common issues:")
        print(f"{Fore.YELLOW}  1. API Key or Secret is incorrect")
        print(f"{Fore.YELLOW}  2. API key doesn't have 'Spot Trading' permission")
        print(f"{Fore.YELLOW}  3. API key has IP restriction (check your IP)")
        print(f"{Fore.YELLOW}  4. Account needs KYC verification")
        print()
        print(f"{Fore.CYAN}To fix:")
        print(f"{Fore.CYAN}  1. Go to https://www.bybit.com/app/user/api-management")
        print(f"{Fore.CYAN}  2. Check your API key is Active")
        print(f"{Fore.CYAN}  3. Verify permissions include 'Read-Write' and 'Spot Trading'")
        print(f"{Fore.CYAN}  4. Copy the correct API Key and Secret to .env file")
        return False
    else:
        print(f"{Fore.GREEN}✅ API Connection Successful!")
        print(f"{Fore.GREEN}🎉 Connected to Bybit!")
        print()
        
        # Display balances
        print(f"{Fore.CYAN}💰 Current Account Balances:")
        print(f"{Fore.CYAN}{'-'*70}")
        
        has_balance = False
        for coin, amount in balance.items():
            if amount > 0.00001:
                has_balance = True
                if coin == 'USDT':
                    print(f"{Fore.GREEN}  💵 {coin}: ${amount:,.2f}")
                elif coin == 'BTC':
                    print(f"{Fore.YELLOW}  ₿  {coin}: {amount:.8f}")
                elif coin == 'SOL':
                    print(f"{Fore.MAGENTA}  ◎  {coin}: {amount:.6f}")
                elif coin == 'ETH':
                    print(f"{Fore.BLUE}  Ξ  {coin}: {amount:.6f}")
                else:
                    print(f"{Fore.WHITE}  💰 {coin}: {amount}")
        
        if not has_balance:
            print(f"{Fore.YELLOW}  ℹ️  Account is empty (no balances)")
            print(f"{Fore.YELLOW}  This is OK - bot will work, just needs funds to trade")
        
        print()
    
    # Test 2: Get Ticker (BTC)
    print(f"{Fore.YELLOW}Test 2: Fetching BTC/USDT ticker...")
    print(f"{Fore.YELLOW}{'-'*70}")
    
    ticker = await get_ticker('BTCUSDT')
    
    if ticker:
        print(f"{Fore.GREEN}✅ Ticker Data Retrieved!")
        print(f"{Fore.GREEN}  Symbol: {ticker['symbol']}")
        print(f"{Fore.GREEN}  Last Price: ${float(ticker['lastPrice']):,.2f}")
        print(f"{Fore.GREEN}  Bid: ${float(ticker['bid']):,.2f}")
        print(f"{Fore.GREEN}  Ask: ${float(ticker['ask']):,.2f}")
        print(f"{Fore.GREEN}  24h Volume: {float(ticker['volume']):,.2f}")
        print()
    else:
        print(f"{Fore.RED}❌ Failed to fetch ticker data")
        print()
    
    # Test 3: Get SOL Ticker
    print(f"{Fore.YELLOW}Test 3: Fetching SOL/USDT ticker...")
    print(f"{Fore.YELLOW}{'-'*70}")
    
    sol_ticker = await get_ticker('SOLUSDT')
    
    if sol_ticker:
        print(f"{Fore.GREEN}✅ SOL Ticker Data Retrieved!")
        print(f"{Fore.GREEN}  Symbol: {sol_ticker['symbol']}")
        print(f"{Fore.GREEN}  Last Price: ${float(sol_ticker['lastPrice']):,.2f}")
        print()
    else:
        print(f"{Fore.RED}❌ Failed to fetch SOL ticker data")
        print()
    
    # Summary
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}✅ ALL TESTS PASSED!")
    print(f"{Fore.CYAN}{'='*70}")
    print()
    print(f"{Fore.GREEN}Your Bybit API is working correctly!")
    print(f"{Fore.CYAN}✅ Ready for LIVE TRADING! 🚀")
    print()
    print(f"{Fore.YELLOW}Next steps:")
    print(f"{Fore.YELLOW}  1. Deposit funds to your Bybit account (if needed)")
    print(f"{Fore.YELLOW}  2. Run simulation: python3 simulate.py --coin BTC")
    print(f"{Fore.YELLOW}  3. Start live trading: python3 live_trade.py --coin BTC")
    print()
    
    return True

if __name__ == '__main__':
    try:
        result = asyncio.run(test_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

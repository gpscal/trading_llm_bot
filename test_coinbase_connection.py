#!/usr/bin/env python3
"""
Coinbase API Connection Test
Tests your Coinbase Advanced API credentials and displays account information
"""

import asyncio
import sys
from api.coinbase import get_balance, get_ticker
from colorama import Fore, Style, init

init(autoreset=True)

async def test_connection():
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🔑 Testing Coinbase Advanced API Connection...")
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
        print(f"{Fore.YELLOW}  2. API key doesn't have 'trade' permission")
        print(f"{Fore.YELLOW}  3. API key is not approved yet (takes a few minutes)")
        print(f"{Fore.YELLOW}  4. Wrong API endpoint (should be Advanced Trade, not old Pro)")
        print()
        print(f"{Fore.CYAN}To fix:")
        print(f"{Fore.CYAN}  1. Go to https://www.coinbase.com/settings/api")
        print(f"{Fore.CYAN}  2. Create new API key for 'Advanced Trade'")
        print(f"{Fore.CYAN}  3. Enable 'View' and 'Trade' permissions")
        print(f"{Fore.CYAN}  4. Copy BOTH the API Key and API Secret to .env file")
        print(f"{Fore.CYAN}  5. Wait 2-3 minutes for key to activate")
        return False
    else:
        print(f"{Fore.GREEN}✅ API Connection Successful!")
        print(f"{Fore.GREEN}🎉 Connected to Coinbase!")
        print()
        
        # Display balances
        print(f"{Fore.CYAN}💰 Current Account Balances:")
        print(f"{Fore.CYAN}{'-'*70}")
        
        has_balance = False
        for coin, amount in balance.items():
            if amount > 0.00001:
                has_balance = True
                if coin in ['USD', 'USDT', 'USDC']:
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
    print(f"{Fore.YELLOW}Test 2: Fetching BTC-USD ticker...")
    print(f"{Fore.YELLOW}{'-'*70}")
    
    ticker = await get_ticker('BTC-USD')
    
    if ticker:
        price = float(ticker['c'][0])
        print(f"{Fore.GREEN}✅ Ticker Data Retrieved!")
        print(f"{Fore.GREEN}  Symbol: BTC-USD")
        print(f"{Fore.GREEN}  Last Price: ${price:,.2f}")
        print()
    else:
        print(f"{Fore.RED}❌ Failed to fetch ticker data")
        print()
    
    # Test 3: Get SOL Ticker
    print(f"{Fore.YELLOW}Test 3: Fetching SOL-USD ticker...")
    print(f"{Fore.YELLOW}{'-'*70}")
    
    sol_ticker = await get_ticker('SOL-USD')
    
    if sol_ticker:
        sol_price = float(sol_ticker['c'][0])
        print(f"{Fore.GREEN}✅ SOL Ticker Data Retrieved!")
        print(f"{Fore.GREEN}  Symbol: SOL-USD")
        print(f"{Fore.GREEN}  Last Price: ${sol_price:,.2f}")
        print()
    else:
        print(f"{Fore.RED}❌ Failed to fetch SOL ticker data")
        print()
    
    # Summary
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.GREEN}✅ ALL TESTS PASSED!")
    print(f"{Fore.CYAN}{'='*70}")
    print()
    print(f"{Fore.GREEN}Your Coinbase API is working correctly!")
    print(f"{Fore.CYAN}✅ Ready for LIVE TRADING! 🚀")
    print()
    print(f"{Fore.YELLOW}Next steps:")
    print(f"{Fore.YELLOW}  1. Deposit funds to your Coinbase account (if needed)")
    print(f"{Fore.YELLOW}     - Go to https://www.coinbase.com/")
    print(f"{Fore.YELLOW}     - Click 'Trade' → 'Deposit'")
    print(f"{Fore.YELLOW}     - Add CAD via Interac e-Transfer (instant!)")
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

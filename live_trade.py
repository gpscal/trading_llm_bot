import asyncio
import argparse
from config.config import CONFIG

# Import based on configured exchange
exchange = CONFIG.get('exchange', 'kraken')
if exchange == 'okx':
    from api.okx import get_ticker
    from utils.okx_balance import initialize_balances
elif exchange == 'coinbase':
    from api.coinbase import get_ticker
    from utils.coinbase_balance import initialize_balances
elif exchange == 'bybit':
    from api.bybit import get_ticker
    from utils.bybit_balance import initialize_balances
else:
    from api.kraken import get_ticker
    from utils.balance import initialize_balances
from utils.logger import setup_logger
from utils.data_fetchers import fetch_initial_price, fetch_and_analyze_historical_data
from utils.shared_state import update_bot_state_safe
from utils.trading_orchestrator import run_trading_loop
from utils.coin_pair_manager import get_coin_pair_manager
from utils.utils import calculate_total_usd

logger = setup_logger('live_trade_logger', 'live_trade.log')

async def live_trade(selected_coin='SOL'):
    coin_manager = get_coin_pair_manager()
    selected_coin = coin_manager.validate_coin(selected_coin)
    
    # Get pair mappings
    pairs = coin_manager.rest_pair_map(['BTC', 'SOL'])
    
    # Fetch initial balances from Kraken
    kraken_balance = await initialize_balances()
    
    # Fetch initial prices
    sol_price = await fetch_initial_price('SOL', prefer_usdt=False)
    btc_price = await fetch_initial_price('BTC', prefer_usdt=True)
    
    if sol_price is None or btc_price is None:
        logger.error(f"Failed to fetch initial prices. SOL={sol_price}, BTC={btc_price}")
        return
    
    # Initialize multi-coin balance structure
    balance = {
        'usdt': kraken_balance.get('usdt', CONFIG['initial_balance_usdt']),
        'selected_coin': selected_coin,
        'coins': {
            'SOL': {
                'amount': kraken_balance.get('sol', 0.0),
                'price': sol_price,
                'indicators': {},
                'historical': [],
                'position_entry_price': None,
                'trailing_high_price': None,
            },
            'BTC': {
                'amount': kraken_balance.get('btc', 0.0),
                'price': btc_price,
                'indicators': {},
                'historical': [],
                'position_entry_price': None,
                'trailing_high_price': None,
            }
        },
        # Backward compatibility
        'sol': kraken_balance.get('sol', 0.0),
        'btc': kraken_balance.get('btc', 0.0),
        'sol_price': sol_price,
        'btc_price': btc_price,
        'last_trade_time': 0,
        'btc_indicators': {},
        'sol_indicators': {},
        'indicators': {}
    }
    
    initial_total_usd = calculate_total_usd(balance)
    balance['initial_total_usd'] = initial_total_usd
    balance['peak_total_usd'] = initial_total_usd
    
    logger.info(
        f"Live trading starting: Trading {selected_coin}, USDT={balance['usdt']:.2f}, "
        f"SOL={balance['sol']:.6f}@{sol_price:.2f}, BTC={balance['btc']:.8f}@{btc_price:.2f}, "
        f"Initial Total USD={initial_total_usd:.2f}"
    )

    await fetch_and_analyze_historical_data(pairs, balance)

    # Update shared state
    update_bot_state_safe({
        "running": True,
        "mode": "live",
        "selected_coin": selected_coin,
        "balance": balance,
        "indicators": {
            "btc": balance.get('coins', {}).get('BTC', {}).get('indicators', {}),
            "sol": balance.get('coins', {}).get('SOL', {}).get('indicators', {})
        }
    })

    # Use unified orchestrator
    await run_trading_loop(
        balance=balance,
        pairs=pairs,
        ticker_fetcher=get_ticker,
        poll_interval=CONFIG['poll_interval'],
        update_history=False,  # Live mode doesn't need full history
        selected_coin=selected_coin
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Live trading with coin selection')
    parser.add_argument('--coin', type=str, default=CONFIG['default_coin'], choices=['SOL', 'BTC'], help='Coin to trade (SOL or BTC)')
    args = parser.parse_args()
    
    logger.info(f"Starting live trading with coin={args.coin}")
    print(f"Starting live trading with coin={args.coin}")
    asyncio.run(live_trade(selected_coin=args.coin))

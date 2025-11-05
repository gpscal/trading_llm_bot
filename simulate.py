import asyncio
import argparse
from initialize_balance import initialize_balance
from websocket_manager import start_websocket
from utils.websocket_handler import handle_websocket_data
from utils.periodic_tasks import print_status_periodically
from trading_loop import trading_loop
from config.config import CONFIG
from utils.data_fetchers import fetch_initial_sol_price, fetch_and_analyze_historical_data
import logging
from utils.shared_state import update_bot_state_safe, get_bot_state_safe, append_log_safe

# Set up logger
logger = logging.getLogger('simulate_logger')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('simulate.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

def parse_args():
    parser = argparse.ArgumentParser(description='Simulation script with customizable initial balance and coin selection.')
    parser.add_argument('--initial_balance_usdt', type=float, default=CONFIG['initial_balance_usdt'], help='Initial balance in USDT')
    parser.add_argument('--initial_balance_sol', type=float, default=CONFIG['initial_balance_sol'], help='Initial balance in SOL')
    parser.add_argument('--initial_balance_btc', type=float, default=CONFIG['initial_balance_btc'], help='Initial balance in BTC')
    parser.add_argument('--coin', type=str, default=CONFIG['default_coin'], choices=['SOL', 'BTC'], help='Coin to trade (SOL or BTC)')
    return parser.parse_args()

async def main(initial_balance_usdt, initial_balance_sol, initial_balance_btc, selected_coin):
    try:
        from utils.data_fetchers import fetch_initial_price
        from utils.coin_pair_manager import get_coin_pair_manager
        
        coin_manager = get_coin_pair_manager()
        selected_coin = coin_manager.validate_coin(selected_coin)
        
        # Fetch initial prices for both coins
        logger.info(f"Fetching initial prices for SOL and BTC...")
        sol_price = await fetch_initial_price('SOL', prefer_usdt=False)
        btc_price = await fetch_initial_price('BTC', prefer_usdt=True)
        
        if sol_price is None or btc_price is None:
            logger.error(f"Failed to fetch initial prices. SOL={sol_price}, BTC={btc_price}")
            append_log_safe("Error: Failed to fetch initial prices. Please check your internet connection and Kraken API availability.")
            return
        
        # Initialize balance structure with multi-coin support
        balance = {
            'usdt': initial_balance_usdt,
            'selected_coin': selected_coin,
            'coins': {
                'SOL': {
                    'amount': initial_balance_sol,
                    'price': sol_price,
                    'indicators': {},
                    'historical': [],
                    'position_entry_price': None,
                    'trailing_high_price': None,
                },
                'BTC': {
                    'amount': initial_balance_btc,
                    'price': btc_price,
                    'indicators': {},
                    'historical': [],
                    'position_entry_price': None,
                    'trailing_high_price': None,
                }
            },
            # Backward compatibility
            'sol': initial_balance_sol,
            'btc': initial_balance_btc,
            'sol_price': sol_price,
            'btc_price': btc_price,
            'btc_momentum': 0.0,
            'confidence': 0.0,
            'initial_total_usd': 0.0,
            'last_trade_time': 0,
            'btc_indicators': {},
            'sol_indicators': {},
            'indicators': {}
        }
        
        from utils.utils import calculate_total_usd
        initial_total_usd = calculate_total_usd(balance)
        balance['initial_total_usd'] = round(initial_total_usd, 2)
        balance['peak_total_usd'] = balance['initial_total_usd']
        
        logger.info(
            f"Simulation starting with coin={selected_coin}, USDT={balance['usdt']}, "
            f"SOL={initial_balance_sol}@{sol_price:.2f}, BTC={initial_balance_btc}@{btc_price:.2f}, "
            f"Total USD={balance['initial_total_usd']:.2f}"
        )
        append_log_safe(
            f"Simulation started: Trading {selected_coin}, Initial balance USDT={balance['usdt']:.2f}, "
            f"SOL={initial_balance_sol:.6f}, BTC={initial_balance_btc:.8f}, Total USD={balance['initial_total_usd']:.2f}"
        )
        
        # Update shared state - mark as running
        update_bot_state_safe({
            "running": True,
            "mode": "simulation",
            "balance": balance
        })
        
        # Get pair mappings from coin manager
        pairs = coin_manager.rest_pair_map(['BTC', 'SOL'])
        
        print("Fetching and analyzing initial historical data...")
        await fetch_and_analyze_historical_data(pairs, balance)
        print("Initial historical data fetched and analyzed")
        
        # Update state again
        update_bot_state_safe({
            "selected_coin": selected_coin,
            "indicators": {
                "btc": balance.get('coins', {}).get('BTC', {}).get('indicators', {}),
                "sol": balance.get('coins', {}).get('SOL', {}).get('indicators', {})
            }
        })
        print(f"Debug: Trading {selected_coin}, Updated indicators in bot_state")
        
        print("Starting websocket...")
        websocket_pairs = coin_manager.websocket_pairs(['BTC', 'SOL'])
        asyncio.create_task(start_websocket(
            url=CONFIG['websocket_url'],
            pairs=websocket_pairs,
            on_data=handle_websocket_data,
            balance=balance
        ))
        
        print("Starting periodic status task...")
        asyncio.create_task(print_status_periodically(balance))
        
        await trading_loop(balance, pairs, CONFIG['poll_interval'], selected_coin)
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        append_log_safe("Simulation stopped by user")
    except Exception as e:
        import traceback
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        print(f"Error in main: {e}")
        append_log_safe(f"Error: {e}")
    finally:
        # Ensure state is cleared when simulation ends
        update_bot_state_safe({"running": False, "mode": None})
        append_log_safe("Simulation ended")

if __name__ == "__main__":
    args = parse_args()
    print(f"Starting simulation with coin={args.coin}, initial balances: USDT={args.initial_balance_usdt}, SOL={args.initial_balance_sol}, BTC={args.initial_balance_btc}")
    asyncio.run(main(args.initial_balance_usdt, args.initial_balance_sol, args.initial_balance_btc, args.coin))
    print("Simulation ended.")

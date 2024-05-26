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

# Set up logger
logger = logging.getLogger('simulate_logger')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('simulate.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

def parse_args():
    parser = argparse.ArgumentParser(description='Simulation script with customizable initial balance.')
    parser.add_argument('--initial_balance_usdt', type=float, default=CONFIG['initial_balance_usdt'], help='Initial balance in USDT')
    parser.add_argument('--initial_balance_sol', type=float, default=CONFIG['initial_balance_sol'], help='Initial balance in SOL')
    return parser.parse_args()

async def main(initial_balance_usdt, initial_balance_sol):
    try:
        # Use specified initial balance
        balance = {
            'usdt': initial_balance_usdt,
            'sol': initial_balance_sol,
            'sol_price': await fetch_initial_sol_price(),
            'btc_price': 0.0,
            'btc_momentum': 0.0,
            'confidence': 0.0,
            'initial_total_usd': 0.0,
            'last_trade_time': 0,
            'btc_indicators': {},
            'sol_indicators': {}
        }
        initial_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
        balance['initial_total_usd'] = round(initial_total_usd, 2)

        pairs = {
            'btc': 'XXBTZUSD',
            'sol': 'SOLUSDT'
        }

        print("Fetching and analyzing initial historical data...")
        await fetch_and_analyze_historical_data(pairs, balance)
        print("Initial historical data fetched and analyzed")

        print("Starting websocket...")
        asyncio.create_task(start_websocket(
            url=CONFIG['websocket_url'],
            pairs=['XBT/USD', 'SOL/USD'],
            on_data=handle_websocket_data,
            balance=balance
        ))

        print("Starting periodic status task...")
        asyncio.create_task(print_status_periodically(balance))

        await trading_loop(balance, pairs, CONFIG['poll_interval'])
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error in main: {e}")

if __name__ == "__main__":
    args = parse_args()
    print("Starting simulation with initial balances: USDT:", args.initial_balance_usdt, "SOL:", args.initial_balance_sol)
    asyncio.run(main(args.initial_balance_usdt, args.initial_balance_sol))
    print("Simulation ended.")

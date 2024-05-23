import numpy as np
from colorama import Fore
from utils.utils import get_timestamp, print_status
from strategies.indicators import calculate_indicators
from api.kraken import get_historical_data
from trade.trade_logic import handle_trade_with_fees

# Initialize global variables
balance = {
    'usdt': 1000,
    'sol': 10,
    'sol_price': None,  # Initialize without a specific price
    'btc_price': None,
    'btc_momentum': 0.0,
    'confidence': 0.0,
    'initial_total_usd': 2784.3  # Example initial total USD value; should be set dynamically
}
btc_previous_price = None
last_sol_price = None
last_trade_time = 0

async def handle_websocket_data(message):
    global btc_previous_price, last_sol_price, last_trade_time, balance

    if isinstance(message, list):
        channel_id, data, _, pair = message

        btc_current_price = None
        sol_current_price = None

        if pair == 'XBT/USD':
            btc_current_price = float(data['c'][0])
            balance['btc_price'] = btc_current_price
            if btc_previous_price is None:
                btc_previous_price = btc_current_price
        elif pair == 'SOL/USD':
            sol_current_price = float(data['c'][0])
            last_sol_price = sol_current_price
            balance['sol_price'] = sol_current_price  # Update the current SOL price

        if btc_current_price is None:
            btc_current_price = btc_previous_price
        if sol_current_price is None:
            sol_current_price = last_sol_price

        if btc_current_price is not None and sol_current_price is not None:
            btc_historical = await get_historical_data('XXBTZUSD', 60)
            sol_historical = await get_historical_data('SOLUSDT', 60)

            if btc_historical and sol_historical:
                btc_indicators, sol_indicators = calculate_indicators(btc_historical, sol_historical)

                result = handle_trade_with_fees(
                    btc_current_price, sol_current_price, btc_previous_price, balance['usdt'], balance['sol'], last_trade_time, btc_indicators, sol_indicators
                )
                balance['usdt'] = result['balance_usdt']
                balance['sol'] = result['balance_sol']
                balance['btc_momentum'] = result['btc_momentum']
                balance['confidence'] = result['confidence']
                btc_previous_price = result['btc_previous_price']
                last_trade_time = result['last_trade_time']

                current_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
                total_gain_usd = current_total_usd - balance['initial_total_usd']
                print_status(get_timestamp(), btc_current_price, sol_current_price, result['btc_momentum'], result['confidence'], balance['usdt'], balance['sol'], current_total_usd, total_gain_usd)
            else:
                print(f"{Fore.RED}[{get_timestamp()}] Error fetching historical data.")
    else:
        event = message.get('event')
        if event == 'heartbeat':
            return
        elif event == 'systemStatus' or event == 'subscriptionStatus':
            print(f"{Fore.YELLOW}[{get_timestamp()}] WebSocket event: {message}")
        else:
            print(f"{Fore.RED}[{get_timestamp()}] Error processing websocket data: {message}")

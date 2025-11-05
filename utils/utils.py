from datetime import datetime
from colorama import Fore, Style
import logging
import json

# Add import
from utils.shared_state import append_log_safe
from utils.alerts import notify

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def setup_unified_logger():
    logger = logging.getLogger('unified_logger')
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        handler = logging.FileHandler('unified.log')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_unified_logger()

def _format_coin_balances(balance):
    coins = balance.get('coins', {})
    if not coins:
        return ""
    summary_parts = []
    for coin, data in coins.items():
        amount = data.get('amount', 0.0)
        price = data.get('price', 0.0)
        summary_parts.append(f"{coin}:{amount:.6f}@{price:.2f}")
    return ", ".join(summary_parts)


def log_and_print_status(balance, current_total_usd, total_gain_usd, coin=None, trade_action=None, volume=None, price=None):
    timestamp = get_timestamp()
    selected_coin = balance.get('selected_coin') or coin
    coin_summary = _format_coin_balances(balance)
    status_message = (
        f"[{timestamp}] Active={selected_coin or 'N/A'} "
        f"USDT:{balance.get('usdt', 0.0):.2f}"
    )
    if coin_summary:
        status_message += f", Coins[{coin_summary}]"
    status_message += f", Total USD: {current_total_usd:.2f}, Total Gain USD: {total_gain_usd:.2f}"
    
    if trade_action and volume is not None and price is not None:
        coin_label = coin or selected_coin or "N/A"
        trade_message = (
            f"[{timestamp}] Trade action: {trade_action} {coin_label}, Volume: {volume:.6f}, Price: {price:.2f}, "
            f"New USDT Balance: {balance.get('usdt', 0.0):.2f}"
        )
        if coin_label and balance.get('coins', {}).get(coin_label):
            trade_message += f", New {coin_label} Balance: {balance['coins'][coin_label]['amount']:.6f}"
        print(trade_message)
        logger.info(trade_message)
        # Append to shared logs
        append_log_safe(trade_message)
        # Alerts
        notify(trade_message)
    
    if not trade_action or volume is None or price is None:
        print(status_message)
        logger.info(status_message)
        # Append to shared logs
        append_log_safe(status_message)

def log_trade(action, volume, price, balance_usdt, balance_coin, coin):
    trade_log = {
        "timestamp": get_timestamp(),
        "action": action,
        "volume": volume,
        "price": price,
        "balance_usdt": balance_usdt,
        "balance_coin": balance_coin,
        "coin": coin
    }
    with open('trade_log.json', 'a') as file:
        json.dump(trade_log, file)
        file.write('\n')

def calculate_total_usd(balance):
    coins = balance.get('coins', {})
    total = balance.get('usdt', 0.0)
    for data in coins.values():
        total += data.get('amount', 0.0) * data.get('price', 0.0)
    return total

def calculate_total_gain_usd(current_total_usd, initial_total_usd):
    return current_total_usd - initial_total_usd

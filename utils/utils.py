from datetime import datetime
from colorama import Fore, Style
import logging
import json

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

def log_and_print_status(balance, current_total_usd, total_gain_usd, trade_action=None, volume=None, price=None):
    timestamp = get_timestamp()
    status_message = (
        f"{Fore.GREEN}[{timestamp}] SOL@{balance.get('sol_price', 0.0):.2f} "
        f"Balance USDT: {balance.get('usdt', 0.0):.2f}, SOL: {balance.get('sol', 0.0):.6f}, Total USD: {current_total_usd:.2f}, "
        f"Total Gain USD: {total_gain_usd:.2f}{Fore.RESET}"
    )
    
    if trade_action and volume is not None and price is not None:
        trade_message = (
            f"{Fore.MAGENTA}[{timestamp}] Trade action: {trade_action}, Volume: {volume:.6f}, Price: {price}, "
            f"New USDT Balance: {balance['usdt']:.2f}, New SOL Balance: {balance['sol']:.6f}{Fore.RESET}"
        )
        print(trade_message)
        logger.info(trade_message)

    if not trade_action or volume is None or price is None:
        print(status_message)
        logger.info(status_message)

def log_trade(action, volume, price, balance_usdt, balance_sol):
    trade_log = {
        "timestamp": get_timestamp(),
        "action": action,
        "volume": volume,
        "price": price,
        "balance_usdt": balance_usdt,
        "balance_sol": balance_sol
    }
    with open('trade_log.json', 'a') as file:
        json.dump(trade_log, file)
        file.write('\n')

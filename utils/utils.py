from datetime import datetime
from colorama import Fore

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_trade(action, volume, price, balance_usdt, balance_sol):
    print(f"{Fore.MAGENTA}[{get_timestamp()}] Trade action: {action}, Volume: {volume:.6f}, Price: {price}, New USDT Balance: {balance_usdt:.2f}, New SOL Balance: {balance_sol:.6f}{Fore.RESET}")

def print_status(timestamp, btc_current_price, sol_current_price, btc_momentum, confidence, balance_usdt, balance_sol, total_usd, total_gain_usd):
    print(f"{Fore.GREEN}[{timestamp}] BTC@{btc_current_price:.2f} SOL@{sol_current_price:.2f} BTC momentum: {btc_momentum:.2f} Confidence level: {confidence:.2f} Balance USDT: {balance_usdt:.2f}, SOL: {balance_sol:.6f}, Total USD: {total_usd:.2f}, Total Gain USD: {total_gain_usd:.2f}{Fore.RESET}")

from colorama import Fore, Style
import numpy as np

def log_debug_info(btc_indicators, sol_indicators, config):
    print(f"{Fore.CYAN}MACD(BTC: {btc_indicators['macd'][1]:.2f} < {config['macd_threshold']['btc']}, SOL: {sol_indicators['macd'][1]:.2f} < {config['macd_threshold']['sol']}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}RSI(BTC: {btc_indicators['rsi']:.2f} < {config['rsi_threshold']}, SOL: {sol_indicators['rsi']:.2f} < {config['rsi_threshold']}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Moving Avg(BTC: {btc_indicators['moving_avg']:.2f} < {config['moving_avg_threshold']['btc']}, SOL: {sol_indicators['moving_avg']:.2f} < {config['moving_avg_threshold']['sol']}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Stochastic Oscillator(BTC: {btc_indicators['stochastic_oscillator']:.2f} < {config['stochastic_oscillator_threshold']['btc']}, SOL: {sol_indicators['stochastic_oscillator']:.2f} < {config['stochastic_oscillator_threshold']['sol']}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}ATR(BTC Mean: {np.mean(btc_indicators['atr']):.2f}, SOL Mean: {np.mean(sol_indicators['atr']):.2f}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}BTC Momentum: {btc_indicators['momentum']:.2f} < {config['btc_momentum_threshold']}{Style.RESET_ALL}")

def log_trade_execution(balance, current_total_usd, total_gain_usd):
    print(f"{Fore.GREEN}Trade executed: USDT: {balance['usdt']:.2f}, SOL: {balance['sol']:.4f}, Total USD: {current_total_usd:.2f}, Total Gain: {total_gain_usd:.2f}{Style.RESET_ALL}")

# config/config.py

import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'initial_balance_usdt': 1000,
    'initial_balance_sol': 10,
    'stop_loss_pct': 5,
    'base_take_profit_pct': 10,
    'max_volume': 10,
    'min_volume': 0.1,
    'poll_interval': 5,
    'cooldown_period': 1,
    'api_key': os.getenv('API_KEY'),
    'api_secret': os.getenv('API_SECRET'),
    'base_url': 'https://api.kraken.com',
    'websocket_url': 'wss://ws.kraken.com/',
    'ma_period': 14,
    'bb_period': 14,
    'macd_fast_period': 12,
    'macd_slow_period': 26,
    'macd_signal_period': 9,
    'rsi_period': 14,
    'atr_period': 14,
    'stochastic_period': 14,
    'adx_period': 14,
    'trade_fee': 0.003,
    'confidence_threshold': 0.05,  # You might want to lower this to allow more trades
    'rsi_threshold': 55,  # Lowered to make it easier to meet the condition
    'macd_threshold': {
        'btc': -100,  # Lowered to make it easier to meet the condition
        'sol': -1  # Lowered to make it easier to meet the condition
    },
    'moving_avg_threshold': {
        'btc': 100000,  # Adjust if needed
        'sol': 1000  # Adjust if needed
    },
    'stochastic_oscillator_threshold': {
        'btc': 80,  # Adjust if needed
        'sol': 80  # Adjust if needed
    },
    'atr_threshold': {
        'btc_mean_factor': 0.1,
        'sol_mean_factor': 0.1
    },
    'btc_momentum_threshold': -500,  # Lowered to make it easier to meet the condition
    'adx_threshold': 1,  # Lowered to make it easier to meet the condition
    'obv_threshold': 1000,  # Adjust if needed
    'indicator_weights': {
        'macd': 0.4,
        'rsi': 0.2,
        'moving_avg': 0.2,
        'stochastic_oscillator': 0.1,
        'atr': 0.1,
        'btc_momentum': 0.2,
        'adx': 0.1,
        'obv': 0.1
    }
}

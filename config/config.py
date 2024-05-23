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
    'cooldown_period': 5,
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
    'stochastic_period': 14
}

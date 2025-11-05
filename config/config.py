# config/config.py

import os
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_COIN = os.getenv('DEFAULT_COIN', 'SOL').upper()
_INITIAL_BALANCE_SOL = float(os.getenv('INITIAL_BALANCE_SOL', 10))
_INITIAL_BALANCE_BTC = float(os.getenv('INITIAL_BALANCE_BTC', 0.01))

CONFIG = {
    'tradable_coins': ['SOL', 'BTC'],
    'default_coin': _DEFAULT_COIN,
    'initial_balance_usdt': float(os.getenv('INITIAL_BALANCE_USDT', 1000)),
    'initial_balance_sol': _INITIAL_BALANCE_SOL,  # backwards compatibility
    'initial_balance_btc': _INITIAL_BALANCE_BTC,
    'initial_coin_balances': {
        'SOL': _INITIAL_BALANCE_SOL,
        'BTC': _INITIAL_BALANCE_BTC,
    },
    'stop_loss_pct': 5,
    'base_take_profit_pct': 10,
    # Additional risk controls
    'trailing_stop_pct': 5,           # Trail stop from highest price since entry
    'max_drawdown_pct': 15,           # Portfolio-level max drawdown before de-risking
    # Legacy single-coin volume settings (use coin_volume_limits instead)
    'max_volume': 10,
    'min_volume': 0.1,
    'coin_volume_limits': {
        'SOL': {
            'min': float(os.getenv('MIN_VOLUME_SOL', 0.1)),
            'max': float(os.getenv('MAX_VOLUME_SOL', 10)),
        },
        'BTC': {
            'min': float(os.getenv('MIN_VOLUME_BTC', 0.0001)),
            'max': float(os.getenv('MAX_VOLUME_BTC', 0.25)),
        },
    },
    'reentry_min_usdt': 5,
    'poll_interval': 5,
    'cooldown_period': 1,
    'api_key': os.getenv('API_KEY'),
    'api_secret': os.getenv('API_SECRET'),
    'base_url': 'https://api.kraken.com',
    'websocket_url': 'wss://ws.kraken.com/',
    'coin_pairs': {
        'SOL': {
            'rest': 'SOLUSDT',      # Kraken REST spot pair (USDT quote)
            'rest_alt': 'SOLUSD',    # Kraken REST alternate pair (USD quote)
            'websocket': 'SOL/USD',
        },
        'BTC': {
            'rest': 'XXBTZUSD',
            'rest_alt': 'XBTUSDT',
            'websocket': 'XBT/USD',
        },
    },
    # Alerts/notifications
    'alerts_enabled': True,
    'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
    'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
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
    'confidence_threshold': 0.01,  # Lowered further (from 0.05) to allow trades with minimal confidence
    'rsi_threshold': 40,  # Lowered (from 55) to make RSI condition easier to meet
    'macd_threshold': {
        'btc': -50,  # Lowered (from -100) for easier MACD condition
        'sol': -0.5  # Lowered (from -1) for easier MACD condition
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
    'btc_momentum_threshold': -100,  # Lowered (from -500) for easier momentum check
    'adx_threshold': 0.5,  # Lowered (from 1) for easier ADX condition
    'obv_threshold': 500,  # Lowered (from 1000) for easier OBV condition
    'indicator_weights': {
        'macd': 0.4,
        'rsi': 0.2,
        'moving_avg': 0.2,
        'stochastic_oscillator': 0.1,
        'atr': 0.1,
        'btc_momentum': 0.2,
        'adx': 0.1,
        'obv': 0.1
    },
    # Machine Learning settings
    'ml_enabled': True,  # Enable ML predictions
    'ml_model_path': 'models/price_predictor.pth',
    'ml_confidence_weight': 0.3,  # How much ML confidence contributes to trade decision
    'ml_min_confidence': 0.6,  # Minimum ML confidence to use prediction
    'ml_use_gpu': True,  # Use GPU for ML inference
    
    # Profitability Prediction settings (learned from trade outcomes)
    'profitability_prediction_enabled': False,  # DISABLED: Model trained on 0% profitable trades, blocks everything
    'profitability_model_path': 'models/profitability_predictor.pth',
    'profitability_norm_path': 'models/profitability_predictor_norm.json',
    'profitability_boost_weight': 0.2,  # Reduced influence (was 0.4)
    'min_profitability_threshold': 0.0,  # Disabled threshold (was 0.3) - model needs retraining with better data
    
    # LLM Trading Advisor settings (integrates LLM_trader for AI-powered trading signals)
    'llm_enabled': True,  # Enable LLM advisor (requires API key configuration)
    'llm_final_authority': True,  # Give LLM final veto power - if HOLD, no trade happens
    'llm_confidence_weight': 0.25,  # How much LLM signal contributes to trade decision (0.0-1.0)
    'llm_model_config_path': 'LLM_trader/config/model_config.ini',  # Path to LLM model config
}

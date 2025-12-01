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
    'poll_interval': 300,  # 5 minutes between trade checks (aligns with Fast LLM min interval)
    'cooldown_period': 300,  # 5 minutes between trades
    'api_key': os.getenv('API_KEY'),
    'api_secret': os.getenv('API_SECRET'),
    
    # Exchange Configuration (Kraken only)
    'exchange': 'kraken',
    
    # Kraken URLs
    'base_url': 'https://api.kraken.com',
    'websocket_url': 'wss://ws.kraken.com/',
    
    'coin_pairs': {
        'SOL': {
            'rest': 'SOLUSDT',
            'rest_alt': 'SOLUSD',
            'websocket': 'SOL/USD',
            'symbol': 'SOL',
        },
        'BTC': {
            'rest': 'XXBTZUSD',
            'rest_alt': 'XBTUSDT',
            'websocket': 'XBT/USD',
            'symbol': 'XBT',
        },
    },
    # Alerts/notifications (Discord only)
    'alerts_enabled': True,
    'discord_bot_token': os.getenv('DISCORD_BOT_TOKEN'),
    'discord_channel_id': os.getenv('DISCORD_CHANNEL_ID'),
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
    'confidence_threshold': 0.35,  # Increased to require stronger signals (was 0.01 - too low!)
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
    
    # LLM Trading Advisor settings (uses local Ollama with DeepSeek-R1)
    'llm_enabled': True,  # Enable LLM advisor
    'llm_final_authority': True,  # Give LLM final veto power - if HOLD, no trade happens
    'llm_confidence_weight': 0.25,  # How much LLM signal contributes to trade decision (0.0-1.0)
    'llm_signal_stability_required': True,  # Require consecutive agreeing signals before trading
    'llm_signal_stability_count': 2,  # Number of consecutive agreeing signals required (2-3 recommended)
    'llm_consensus_required': True,  # Require BOTH Fast LLM and Deep Analysis to agree (BUY or SELL)
    
    # Ollama Fast LLM settings
    'ollama_base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),  # Ollama API URL
    'ollama_model': os.getenv('OLLAMA_MODEL', 'deepseek-r1:8b'),  # Fast LLM model
    'ollama_timeout': 120,  # 2 minutes timeout for model response (DeepSeek-R1:8b is slower)
    
    # Deep Analysis settings (comprehensive analysis using Claude AI + RAG)
    'deep_analysis_enabled': True,  # Enable deep analyzer for comprehensive market context
    'deep_analysis_interval': 7200,  # Analysis interval in seconds (2 hours)
    'deep_analysis_cache_duration': 7200,  # Cache duration in seconds
    'deep_analysis_model': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),  # Primary model from .env
    'deep_analysis_fallback_model': 'anthropic/claude-3.5-sonnet',  # OpenRouter fallback
    'deep_analysis_confidence_weight': 0.35,  # Weight for deep analysis in trade decisions
    'deep_analysis_veto_power': True,  # Deep analysis can veto trades if high confidence
    'deep_analysis_min_agreement': 0.6,  # Minimum agreement between fast/deep for high confidence
    
    # News API settings (CryptoCompare primary, NewsAPI.ai fallback)
    'news_api_enabled': True,  # Enable news fetching and sentiment analysis
    'cryptocompare_api_key': os.getenv('CRYPTOCOMPARE_API_KEY'),  # CryptoCompare API key (primary)
    'cryptocompare_base_url': 'https://min-api.cryptocompare.com/data',  # CryptoCompare base URL
    'news_api_key': os.getenv('NEWS_API_AI'),  # NewsAPI.ai API key (fallback)
    'news_api_base_url': 'https://eventregistry.org/api/v1',  # NewsAPI.ai base URL
    'news_api_cache_duration': 3600,  # Cache news for 1 hour (news changes less frequently)
    'news_api_rate_limit': 100,  # Max requests per day (adjust based on your plan)
    'news_api_max_articles': 10,  # Maximum articles to fetch per request
    'news_api_timeout': 15,  # Request timeout in seconds
    'news_crypto_keywords': ['bitcoin', 'ethereum', 'solana', 'crypto', 'cryptocurrency', 'blockchain'],
    'news_sentiment_weight': 0.15,  # How much news sentiment affects trading decisions
    
    # API Keys (loaded from environment or .env file)
    'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
    'anthropic_model': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),  # Model name from .env
    'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
}

import asyncio
from api.kraken import get_ticker
from utils.balance import initialize_balances
from config.config import CONFIG
from utils.logger import setup_logger
from utils.data_fetchers import fetch_initial_sol_price, fetch_and_analyze_historical_data
from utils.shared_state import update_bot_state_safe
from utils.trading_orchestrator import run_trading_loop

logger = setup_logger('live_trade_logger', 'live_trade.log')

async def live_trade():
    pairs = {
        'btc': 'XXBTZUSD',
        'sol': 'SOLUSD'
    }
    balance = await initialize_balances()
    balance['sol_price'] = await fetch_initial_sol_price()
    balance['btc_price'] = 0.0
    balance['last_trade_time'] = 0
    balance['btc_indicators'] = {}
    balance['sol_indicators'] = {}

    # Ensuring SOL initial price is only fetched once
    sol_initial_price = balance['sol_price']
    logger.info(f"Initial SOL price used: {sol_initial_price}")

    initial_total_usd = balance['usdt'] + balance['sol'] * sol_initial_price
    balance['initial_total_usd'] = initial_total_usd
    # Risk/equity tracking fields
    balance['peak_total_usd'] = balance['initial_total_usd']
    balance['position_entry_price'] = None
    balance['trailing_high_price'] = None

    await fetch_and_analyze_historical_data(pairs, balance)

    logger.info(f"Initial Balances: USDT: {balance['usdt']}, SOL: {balance['sol']}, Initial Total USD: {balance['initial_total_usd']}")

    # Update shared state
    update_bot_state_safe({
        "balance": balance,
        "indicators": {
            "btc": balance.get('btc_indicators', {}),
            "sol": balance.get('sol_indicators', {})
        }
    })

    # Use unified orchestrator
    await run_trading_loop(
        balance=balance,
        pairs=pairs,
        ticker_fetcher=get_ticker,
        poll_interval=CONFIG['poll_interval'],
        update_history=False  # Live mode doesn't need full history
    )

if __name__ == '__main__':
    logger.info("Starting live trading")
    asyncio.run(live_trade())

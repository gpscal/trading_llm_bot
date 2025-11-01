from utils.trading_orchestrator import run_trading_loop

# This function is kept for backwards compatibility
# It now delegates to the unified orchestrator
async def trading_loop(balance, pairs, poll_interval):
    """Legacy trading loop - delegates to unified orchestrator."""
    await run_trading_loop(
        balance=balance,
        pairs=pairs,
        ticker_fetcher=None,  # Simulation mode uses websocket prices
        poll_interval=poll_interval,
        update_history=True  # Simulation mode tracks full history for dashboard
    )

"""Unified trading orchestrator for live and simulation modes.

This module provides a common polling loop that handles:
- Historical data fetching and indicator calculation
- Price updates and trade execution
- State updates and logging
- Risk metrics tracking
"""

import asyncio
import time
from typing import Callable, Dict, Optional
from config.config import CONFIG
from utils.logger import setup_logger
from utils.data_fetchers import fetch_and_analyze_historical_data
from trade.trade_logic import handle_trade_with_fees
from utils.utils import log_and_print_status
from utils.shared_state import update_bot_state_safe, get_bot_state_safe

logger = setup_logger('orchestrator_logger', 'orchestrator.log')


async def run_trading_loop(
    balance: Dict,
    pairs: Dict[str, str],
    ticker_fetcher: Optional[Callable] = None,
    poll_interval: Optional[float] = None,
    update_history: bool = False
) -> None:
    """Unified trading loop for both live and simulation modes.
    
    Args:
        balance: Balance dict with usdt, sol, prices, indicators, etc.
        pairs: Dict mapping 'btc' and 'sol' to Kraken pair symbols
        ticker_fetcher: Optional async function to fetch current tickers (for live mode)
        poll_interval: Seconds between poll cycles (defaults to CONFIG['poll_interval'])
        update_history: If True, append to price/equity/drawdown history (for simulation dashboard)
    """
    poll_interval = poll_interval or CONFIG['poll_interval']
    initial_sol_price = balance.get('sol_price', 0.0)
    initial_total_usd = balance.get('initial_total_usd', 0.0)
    
    logger.info(f"Starting trading loop with poll_interval={poll_interval}s, update_history={update_history}")
    
    while True:
        try:
            # Sleep first to avoid immediate execution
            await asyncio.sleep(poll_interval)
            
            # Fetch and analyze historical data to update indicators
            await fetch_and_analyze_historical_data(pairs, balance)
            
            # Get current prices (from ticker API for live, from balance for sim)
            if ticker_fetcher:
                # Live mode: fetch fresh ticker data
                btc_ticker = await ticker_fetcher(pairs['btc'])
                sol_ticker = await ticker_fetcher(pairs['sol'])
                if not btc_ticker or not sol_ticker:
                    logger.error("Failed to fetch ticker data, skipping cycle")
                    continue
                btc_price = float(btc_ticker['c'][0])
                sol_price = float(sol_ticker['c'][0])
                balance['btc_price'] = btc_price
                balance['sol_price'] = sol_price
            else:
                # Simulation mode: use prices from balance (updated by websocket)
                btc_price = balance.get('btc_price', 0.0)
                sol_price = balance.get('sol_price', 0.0)
            
            # Get indicators from balance (populated by fetch_and_analyze_historical_data)
            btc_indicators = balance.get('btc_indicators', {})
            sol_indicators = balance.get('sol_indicators', {})
            
            if not btc_price or not sol_price:
                logger.warning(f"Missing prices: BTC={btc_price}, SOL={sol_price}, skipping trade")
                continue
            
            if not btc_indicators or not sol_indicators:
                logger.warning("Indicators not yet available, skipping trade")
                continue
            
            # Execute trade logic
            balance['usdt'], balance['sol'], balance['last_trade_time'] = handle_trade_with_fees(
                btc_price, sol_price,
                balance['usdt'], balance['sol'], balance.get('last_trade_time', 0),
                btc_indicators, sol_indicators,
                initial_sol_price, initial_total_usd,
                balance
            )
            
            # Calculate metrics
            current_total_usd = balance['usdt'] + balance['sol'] * sol_price
            total_gain_usd = current_total_usd - initial_total_usd
            
            # Update peak equity for drawdown calculation
            balance['peak_total_usd'] = max(
                balance.get('peak_total_usd', current_total_usd),
                current_total_usd
            )
            peak = balance['peak_total_usd']
            drawdown_pct = 0.0 if peak == 0 else max(0.0, (peak - current_total_usd) / peak * 100.0)
            
            # Log status
            log_and_print_status(balance, current_total_usd, total_gain_usd)
            
            # Update shared state
            update_data = {
                "balance": balance.copy(),
                "indicators": {
                    "btc": btc_indicators.copy(),
                    "sol": sol_indicators.copy()
                }
            }
            
            # Optionally update history for dashboard charts (simulation mode)
            if update_history:
                now_ts = time.time()
                bot_state = get_bot_state_safe()
                update_data.update({
                    "price_history": bot_state.get("price_history", []) + [{"time": now_ts, "price": sol_price}],
                    "btc_price_history": bot_state.get("btc_price_history", []) + [{"time": now_ts, "price": btc_price}],
                    "equity_history": bot_state.get("equity_history", []) + [{"time": now_ts, "equity": current_total_usd}],
                    "drawdown_history": bot_state.get("drawdown_history", []) + [{"time": now_ts, "drawdown_pct": drawdown_pct}],
                    "indicator_history": {
                        "btc": bot_state.get("indicator_history", {}).get("btc", []) + [{
                            "time": now_ts,
                            "moving_avg": btc_indicators.get('moving_avg'),
                            "bb_upper": (btc_indicators.get('bollinger_bands') or (None, None))[0],
                            "bb_lower": (btc_indicators.get('bollinger_bands') or (None, None))[1],
                            "macd": (btc_indicators.get('macd') or (None, None))[0],
                            "macd_signal": (btc_indicators.get('macd') or (None, None))[1],
                            "rsi": btc_indicators.get('rsi'),
                            "stoch": btc_indicators.get('stochastic_oscillator'),
                            "atr": btc_indicators.get('atr'),
                            "momentum": btc_indicators.get('momentum')
                        }],
                        "sol": bot_state.get("indicator_history", {}).get("sol", []) + [{
                            "time": now_ts,
                            "moving_avg": sol_indicators.get('moving_avg'),
                            "bb_upper": (sol_indicators.get('bollinger_bands') or (None, None))[0],
                            "bb_lower": (sol_indicators.get('bollinger_bands') or (None, None))[1],
                            "macd": (sol_indicators.get('macd') or (None, None))[0],
                            "macd_signal": (sol_indicators.get('macd') or (None, None))[1],
                            "rsi": sol_indicators.get('rsi'),
                            "stoch": sol_indicators.get('stochastic_oscillator'),
                            "atr": sol_indicators.get('atr'),
                            "momentum": sol_indicators.get('momentum')
                        }]
                    }
                })
            
            update_bot_state_safe(update_data)
            
        except Exception as e:
            logger.error(f"Error in trading loop cycle: {e}", exc_info=True)
            await asyncio.sleep(5)  # Brief pause before retry

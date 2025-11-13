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
    update_history: bool = False,
    selected_coin: Optional[str] = None
) -> None:
    """Unified trading loop for both live and simulation modes.
    
    Args:
        balance: Balance dict with usdt, coins, prices, indicators, etc.
        pairs: Dict mapping coin symbols to Kraken pair symbols (e.g., {'BTC': 'XXBTZUSD', 'SOL': 'SOLUSDT'})
        ticker_fetcher: Optional async function to fetch current tickers (for live mode)
        poll_interval: Seconds between poll cycles (defaults to CONFIG['poll_interval'])
        update_history: If True, append to price/equity/drawdown history (for simulation dashboard)
        selected_coin: The coin to trade (defaults to CONFIG default_coin)
    """
    poll_interval = poll_interval or CONFIG['poll_interval']
    trade_coin = (selected_coin or balance.get('selected_coin') or CONFIG.get('default_coin', 'SOL')).upper()
    balance['selected_coin'] = trade_coin
    
    initial_total_usd = balance.get('initial_total_usd', 0.0)
    initial_coin_price = balance.get('coins', {}).get(trade_coin, {}).get('price', 0.0)
    
    logger.info(f"Starting trading loop with poll_interval={poll_interval}s, update_history={update_history}")
    
    # Continue running until explicitly stopped
    while True:
        # Check if we should stop (only stop if explicitly set to False)
        state = get_bot_state_safe()
        if not state.get('running', True):
            logger.info("Running state set to False, stopping trading loop")
            break
        
        try:
            # Sleep first to avoid immediate execution
            await asyncio.sleep(poll_interval)
            
            # Fetch and analyze historical data to update indicators
            await fetch_and_analyze_historical_data(pairs, balance)
            
            # Get current prices (from ticker API for live, from balance for sim)
            if ticker_fetcher:
                # Live mode: fetch fresh ticker data for all pairs
                prices = {}
                for coin, pair in pairs.items():
                    ticker = await ticker_fetcher(pair)
                    if not ticker:
                        logger.error(f"Failed to fetch ticker data for {coin}, skipping cycle")
                        continue
                    prices[coin] = float(ticker['c'][0])
                    if coin in balance.get('coins', {}):
                        balance['coins'][coin]['price'] = prices[coin]
                
                # Backward compatibility
                balance['btc_price'] = prices.get('BTC', 0.0)
                balance['sol_price'] = prices.get('SOL', 0.0)
            else:
                # Simulation mode: use prices from balance (updated by websocket)
                prices = {coin: data.get('price', 0.0) for coin, data in balance.get('coins', {}).items()}
                balance['btc_price'] = prices.get('BTC', 0.0)
                balance['sol_price'] = prices.get('SOL', 0.0)
            
            btc_price = prices.get('BTC', balance.get('btc_price', 0.0))
            sol_price = prices.get('SOL', balance.get('sol_price', 0.0))
            
            # Get indicators from balance (populated by fetch_and_analyze_historical_data)
            btc_indicators = balance.get('coins', {}).get('BTC', {}).get('indicators') or balance.get('btc_indicators', {})
            sol_indicators = balance.get('coins', {}).get('SOL', {}).get('indicators') or balance.get('sol_indicators', {})
            
            if not btc_price or not sol_price:
                logger.warning(f"Missing prices: BTC={btc_price}, SOL={sol_price}, skipping trade")
                continue
            
            if not btc_indicators or not sol_indicators:
                logger.warning("Indicators not yet available, skipping trade")
                continue
            
            # Execute trade logic
            coin_balance = balance.get('coins', {}).get(trade_coin, {}).get('amount', 0.0)
            old_last_trade_time = balance.get('last_trade_time', 0)
            balance['usdt'], new_coin_balance, balance['last_trade_time'] = await handle_trade_with_fees(
                btc_price, sol_price,
                balance['usdt'], coin_balance, old_last_trade_time,
                btc_indicators, sol_indicators,
                initial_coin_price, initial_total_usd,
                balance,
                selected_coin=trade_coin
            )
            
            # Update coin balance in structure
            if trade_coin in balance.get('coins', {}):
                balance['coins'][trade_coin]['amount'] = new_coin_balance
            
            # Backward compatibility
            balance['sol'] = balance.get('coins', {}).get('SOL', {}).get('amount', 0.0)
            balance['btc'] = balance.get('coins', {}).get('BTC', {}).get('amount', 0.0)
            
            # Calculate metrics
            from utils.utils import calculate_total_usd
            current_total_usd = calculate_total_usd(balance)
            total_gain_usd = current_total_usd - initial_total_usd
            
            # Update peak equity for drawdown calculation
            balance['peak_total_usd'] = max(
                balance.get('peak_total_usd', current_total_usd),
                current_total_usd
            )
            peak = balance['peak_total_usd']
            drawdown_pct = 0.0 if peak == 0 else max(0.0, (peak - current_total_usd) / peak * 100.0)
            
            # Only log status if:
            # 1. Trade time changed (trade was attempted/executed), OR
            # 2. We're not in cooldown (to show periodic status), OR  
            # 3. It's been more than 5 minutes since last status log
            now = time.time()
            should_log_status = (
                balance['last_trade_time'] != old_last_trade_time or  # Trade attempted
                (now - old_last_trade_time) >= CONFIG['cooldown_period'] or  # Not in cooldown
                (now - balance.get('last_status_log', 0)) >= 300  # 5 min since last status
            )
            
            if should_log_status:
                log_and_print_status(balance, current_total_usd, total_gain_usd, coin=trade_coin)
                balance['last_status_log'] = now
            
            # Update shared state - ensure running flag is set
            update_data = {
                "running": True,  # Ensure this stays True during trading
                "selected_coin": trade_coin,
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
                primary_price = prices.get(trade_coin, 0.0)
                update_data.update({
                    "price_history": bot_state.get("price_history", []) + [{"time": now_ts, "price": primary_price}],
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
            # Check running state again after error
            state = get_bot_state_safe()
            if not state.get('running', True):
                logger.info("Running state set to False after error, stopping trading loop")
                break
            await asyncio.sleep(5)  # Brief pause before retry

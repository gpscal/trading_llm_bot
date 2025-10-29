import asyncio
import numpy as np
from utils.data_fetchers import fetch_and_analyze_historical_data
from utils.logger import setup_logger
from trade.trade_logic import handle_trade_with_fees
from utils.utils import log_and_print_status
from config.config import CONFIG
from utils.shared_state import update_bot_state, bot_state
import time

logger = setup_logger('main_logger', 'main.log')

async def trading_loop(balance, pairs, poll_interval):
    initial_sol_price = balance['sol_price']
    while True:
        logger.debug("Top of the main loop")
        
        await asyncio.sleep(poll_interval)
        logger.debug("After sleep in the main loop")
        
        await fetch_and_analyze_historical_data(pairs, balance)
        
        btc_price = balance['btc_price']
        sol_price = balance['sol_price']
        btc_indicators = balance.get('btc_indicators', {})
        sol_indicators = balance.get('sol_indicators', {})
        
        if btc_price and sol_price and btc_indicators and sol_indicators:
            logger.debug(f"BTC Price: {btc_price}, SOL Price: {sol_price}")
            logger.debug(f"BTC Indicators: {btc_indicators}")
            logger.debug(f"SOL Indicators: {sol_indicators}")
            
            balance['usdt'], balance['sol'], balance['last_trade_time'] = handle_trade_with_fees(
                btc_price, sol_price, balance['usdt'], balance['sol'], balance['last_trade_time'], btc_indicators, sol_indicators, initial_sol_price, balance['initial_total_usd'], balance
            )
        
        current_total_usd = balance['usdt'] + balance['sol'] * balance['sol_price']
        total_gain_usd = current_total_usd - balance['initial_total_usd']
        # Update peak and drawdown
        balance['peak_total_usd'] = max(balance.get('peak_total_usd', current_total_usd), current_total_usd)
        peak = balance['peak_total_usd'] if balance['peak_total_usd'] else current_total_usd
        drawdown_pct = 0.0 if peak == 0 else max(0.0, (peak - current_total_usd) / peak * 100.0)
        
        log_and_print_status(balance, current_total_usd, total_gain_usd)
        
        # Update shared state
        now_ts = time.time()
        update_bot_state({
            "balance": balance,
            "indicators": {"btc": btc_indicators, "sol": sol_indicators},
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

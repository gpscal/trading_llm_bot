import time
import numpy as np
from config.config import CONFIG
from utils.utils import get_timestamp, log_trade, log_and_print_status
from trade.volume_calculator import calculate_volume
from utils.logger import setup_logger
from utils.alerts import notify

# Add import
from utils.shared_state import append_log_safe

logger = setup_logger('trade_logic_logger', 'trade_logic.log')

def execute_trade(action, volume, price, balance_usdt, balance_sol, trade_fee):
    if action == 'buy':
        total_cost = volume * price * (1 + trade_fee)
        if balance_usdt < total_cost:
            volume = balance_usdt / (price * (1 + trade_fee))
            total_cost = volume * price * (1 + trade_fee)
        balance_usdt -= total_cost
        balance_sol += volume
    elif action == 'sell':
        if balance_sol < volume:
            volume = balance_sol
        total_revenue = volume * price * (1 - trade_fee)
        balance_usdt += total_revenue
        balance_sol -= volume
    return balance_usdt, balance_sol

def handle_trade_with_fees(btc_current_price, sol_current_price, balance_usdt, balance_sol, last_trade_time, btc_indicators, sol_indicators, initial_sol_price, initial_total_usd, balance=None):
    try:
        now = time.time()

        if now - last_trade_time < CONFIG['cooldown_period']:
            logger.info(f"{get_timestamp()} Cooldown period active. Skipping trade.")
            return balance_usdt, balance_sol, last_trade_time

        # --- Portfolio-level risk: max drawdown ---
        if balance is not None:
            current_total_usd = balance_usdt + balance_sol * sol_current_price
            # Initialize peak if missing
            peak_total_usd = balance.get('peak_total_usd', current_total_usd)
            if current_total_usd > peak_total_usd:
                peak_total_usd = current_total_usd
                balance['peak_total_usd'] = peak_total_usd
            max_drawdown_pct = CONFIG.get('max_drawdown_pct', 0) / 100.0
            if max_drawdown_pct > 0 and current_total_usd <= peak_total_usd * (1 - max_drawdown_pct) and balance_sol > 0:
                # De-risk: liquidate SOL position
                trade_fee = CONFIG['trade_fee']
                volume_to_sell = balance_sol
                pre_usdt, pre_sol = balance_usdt, balance_sol
                balance_usdt, balance_sol = execute_trade('sell', volume_to_sell, sol_current_price, balance_usdt, balance_sol, trade_fee)
                msg = f"[{get_timestamp()}] Max drawdown hit. Liquidated {pre_sol:.6f} SOL at {sol_current_price:.2f}. USDT {pre_usdt:.2f} -> {balance_usdt:.2f}"
                logger.info(msg)
                append_log_safe(msg)
                notify(msg)
                if balance is not None:
                    balance['position_entry_price'] = None
                    balance['trailing_high_price'] = None
                return balance_usdt, balance_sol, now

        macd_condition = (
            btc_indicators['macd'][0] < CONFIG['macd_threshold']['btc'] and 
            sol_indicators['macd'][0] < CONFIG['macd_threshold']['sol']
        )
        rsi_condition = (
            btc_indicators['rsi'] < CONFIG['rsi_threshold'] and 
            sol_indicators['rsi'] < CONFIG['rsi_threshold']
        )
        adx_condition = (
            btc_indicators.get('adx', 0) > CONFIG['adx_threshold'] and 
            sol_indicators.get('adx', 0) > CONFIG['adx_threshold']
        )
        obv_condition = (
            btc_indicators['obv'] > CONFIG['obv_threshold'] and 
            sol_indicators['obv'] > CONFIG['obv_threshold']
        )

        confidence = 0
        if macd_condition:
            confidence += CONFIG['indicator_weights']['macd']
        if rsi_condition:
            confidence += CONFIG['indicator_weights']['rsi']
        if adx_condition:
            confidence += CONFIG['indicator_weights']['adx']
        if obv_condition:
            confidence += CONFIG['indicator_weights']['obv']

        logger.info(f"Indicators - MACD: {btc_indicators['macd']}, {sol_indicators['macd']} | RSI: {btc_indicators['rsi']}, {sol_indicators['rsi']} | ADX: {btc_indicators.get('adx', 'N/A')}, {sol_indicators.get('adx', 'N/A')} | OBV: {btc_indicators['obv']}, {sol_indicators['obv']} | Confidence: {confidence:.2f}")
        
        # Append to shared logs
        confidence_message = f"[{get_timestamp()}] Confidence: {confidence:.2f}"
        append_log_safe(confidence_message)

        if confidence < CONFIG['confidence_threshold']:
            logger.info(f"{get_timestamp()} Confidence too low. Skipping trade.")
            return balance_usdt, balance_sol, last_trade_time

        volume = calculate_volume(sol_current_price, balance_usdt, CONFIG)
        trade_action = 'buy' if btc_indicators['momentum'] > 0 else 'sell'
        trade_fee = CONFIG['trade_fee']

        if trade_action == 'sell' and balance_sol < volume:
            volume = balance_sol
        elif trade_action == 'buy' and balance_usdt < volume * sol_current_price * (1 + trade_fee):
            volume = balance_usdt / (sol_current_price * (1 + trade_fee))

        if volume <= 0:
            logger.info(f"{get_timestamp()} Volume too low to execute trade: {volume}. Transaction did not go through.")
            return balance_usdt, balance_sol, last_trade_time

        # --- Position-based risk controls (if holding SOL) ---
        if balance is not None and balance_sol > 0:
            entry = balance.get('position_entry_price')
            trailing_high = balance.get('trailing_high_price', entry)
            if entry:
                # Update trailing high
                trailing_high = max(trailing_high or entry, sol_current_price)
                balance['trailing_high_price'] = trailing_high
                # Stop-loss
                if CONFIG.get('stop_loss_pct'):
                    if (entry - sol_current_price) / entry >= CONFIG['stop_loss_pct'] / 100.0:
                        sell_vol = balance_sol
                        pre_sol = balance_sol
                        balance_usdt, balance_sol = execute_trade('sell', sell_vol, sol_current_price, balance_usdt, balance_sol, trade_fee)
                        msg = f"[{get_timestamp()}] Stop-loss triggered. Sold {pre_sol:.6f} SOL at {sol_current_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        balance['position_entry_price'] = None
                        balance['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_sol, last_trade_time
                # Take-profit
                if CONFIG.get('base_take_profit_pct'):
                    if (sol_current_price - entry) / entry >= CONFIG['base_take_profit_pct'] / 100.0:
                        sell_vol = balance_sol
                        pre_sol = balance_sol
                        balance_usdt, balance_sol = execute_trade('sell', sell_vol, sol_current_price, balance_usdt, balance_sol, trade_fee)
                        msg = f"[{get_timestamp()}] Take-profit triggered. Sold {pre_sol:.6f} SOL at {sol_current_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        balance['position_entry_price'] = None
                        balance['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_sol, last_trade_time
                # Trailing stop
                if CONFIG.get('trailing_stop_pct') and trailing_high:
                    if sol_current_price <= trailing_high * (1 - CONFIG['trailing_stop_pct'] / 100.0):
                        sell_vol = balance_sol
                        pre_sol = balance_sol
                        balance_usdt, balance_sol = execute_trade('sell', sell_vol, sol_current_price, balance_usdt, balance_sol, trade_fee)
                        msg = f"[{get_timestamp()}] Trailing stop triggered. Sold {pre_sol:.6f} SOL at {sol_current_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        balance['position_entry_price'] = None
                        balance['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_sol, last_trade_time

        pre_balance_sol = balance_sol
        balance_usdt, balance_sol = execute_trade(trade_action, volume, sol_current_price, balance_usdt, balance_sol, trade_fee)
        # Update position entry/trailing on fresh long entry
        if balance is not None and trade_action == 'buy' and pre_balance_sol == 0 and balance_sol > 0:
            balance['position_entry_price'] = sol_current_price
            balance['trailing_high_price'] = sol_current_price
        
        current_total_usd = balance_usdt + balance_sol * sol_current_price
        total_gain_usd = current_total_usd - initial_total_usd
        
        log_and_print_status({'usdt': balance_usdt, 'sol': balance_sol, 'sol_price': sol_current_price}, current_total_usd, total_gain_usd, trade_action, volume, sol_current_price)
        
        last_trade_time = now
        return balance_usdt, balance_sol, last_trade_time
    except Exception as e:
        logger.error(f"Error in handle_trade_with_fees: {e}")
        return balance_usdt, balance_sol, last_trade_time

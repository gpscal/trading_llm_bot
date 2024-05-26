import time
import numpy as np
from config.config import CONFIG
from utils.utils import get_timestamp, log_trade, log_and_print_status
from trade.volume_calculator import calculate_volume
from utils.logger import setup_logger

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

def handle_trade_with_fees(btc_current_price, sol_current_price, balance_usdt, balance_sol, last_trade_time, btc_indicators, sol_indicators, initial_sol_price, initial_total_usd):
    try:
        now = time.time()

        if now - last_trade_time < CONFIG['cooldown_period']:
            logger.info(f"{get_timestamp()} Cooldown period active. Skipping trade.")
            return balance_usdt, balance_sol, last_trade_time

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

        balance_usdt, balance_sol = execute_trade(trade_action, volume, sol_current_price, balance_usdt, balance_sol, trade_fee)
        
        current_total_usd = balance_usdt + balance_sol * sol_current_price
        total_gain_usd = current_total_usd - initial_total_usd
        
        log_and_print_status({'usdt': balance_usdt, 'sol': balance_sol, 'sol_price': sol_current_price}, current_total_usd, total_gain_usd, trade_action, volume, sol_current_price)
        
        last_trade_time = now
        return balance_usdt, balance_sol, last_trade_time
    except Exception as e:
        logger.error(f"Error in handle_trade_with_fees: {e}")
        return balance_usdt, balance_sol, last_trade_time

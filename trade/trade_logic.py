import time
import numpy as np
from config.config import CONFIG
from utils.utils import get_timestamp, log_trade, log_and_print_status
from trade.volume_calculator import calculate_volume
from utils.logger import setup_logger
from utils.alerts import notify

# Add imports
from utils.shared_state import append_log_safe
# ML import is lazy-loaded to avoid circular dependencies

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
        
        # Add ML prediction if enabled
        ml_confidence_boost = 0.0
        ml_prediction = None
        if CONFIG.get('ml_enabled', False):
            try:
                # Lazy import to avoid circular dependencies
                from ml.ml_predictor_manager import get_ml_predictor_manager
                ml_manager = get_ml_predictor_manager(
                    CONFIG.get('ml_model_path', 'models/price_predictor.pth'),
                    CONFIG.get('ml_use_gpu', True)
                )
                
                # Get historical data for ML prediction
                # Note: This is simplified - in production, maintain historical data cache
                from api.kraken import get_historical_data
                import asyncio
                
                # Fetch recent data for ML (we need at least 60 candles)
                try:
                    # Try to get historical data for ML
                    # In production, this should be cached and updated incrementally
                    sol_historical = None  # Will be fetched if needed
                    btc_historical = None
                    
                    # For now, skip ML if we don't have historical data readily available
                    # This will be improved in production with proper data caching
                    ml_prediction = None
                except Exception as e:
                    logger.debug(f"ML prediction skipped (no historical data cache): {e}")
                    ml_prediction = None
                
                if ml_prediction and ml_prediction['confidence'] >= CONFIG.get('ml_min_confidence', 0.6):
                    # ML predicts same direction as indicators
                    ml_direction = ml_prediction['direction']
                    indicator_direction = 'up' if btc_indicators['momentum'] > 0 else 'down'
                    
                    if ml_direction == indicator_direction or ml_direction == 'hold':
                        # ML confirms indicators, boost confidence
                        ml_confidence_boost = ml_prediction['confidence'] * CONFIG.get('ml_confidence_weight', 0.3)
                    elif ml_direction != indicator_direction:
                        # ML contradicts indicators, reduce confidence
                        ml_confidence_boost = -ml_prediction['confidence'] * CONFIG.get('ml_confidence_weight', 0.2)
                    
                    logger.info(f"ML Prediction - Direction: {ml_direction}, Confidence: {ml_prediction['confidence']:.2f}, Boost: {ml_confidence_boost:.2f}")
                    append_log_safe(f"ML: {ml_direction} (confidence: {ml_prediction['confidence']:.2f})")
                
            except Exception as e:
                logger.error(f"ML prediction error: {e}")
        
        # Add profitability prediction if enabled
        profitability_prediction = None
        profitability_boost = 0.0
        if CONFIG.get('profitability_prediction_enabled', False):
            try:
                # Lazy import to avoid circular dependencies
                from ml.profitability_predictor_manager import get_profitability_predictor_manager
                profitability_manager = get_profitability_predictor_manager(
                    CONFIG.get('profitability_model_path', 'models/profitability_predictor.pth'),
                    CONFIG.get('profitability_norm_path', 'models/profitability_predictor_norm.json'),
                    CONFIG.get('ml_use_gpu', True)
                )
                
                # Get historical data for profitability prediction
                # In production, this should be cached
                try:
                    # Try to get historical data from balance if available
                    sol_historical = balance.get('sol_historical') if balance else None
                    btc_historical = balance.get('btc_historical') if balance else None
                    
                    # If not available in balance, we'll skip profitability prediction for now
                    # (In production, maintain a historical data cache)
                    if sol_historical and len(sol_historical) >= 60:
                        profitability_prediction = profitability_manager.predict_profitability(
                            sol_historical, btc_historical
                        )
                        
                        if profitability_prediction:
                            profitability_prob = profitability_prediction['probability']
                            is_profitable = profitability_prediction['profitable']
                            
                            # Boost confidence if model predicts profitable trade
                            if is_profitable:
                                # Higher probability = higher boost
                                profitability_boost = (profitability_prob - 0.5) * CONFIG.get('profitability_boost_weight', 0.4)
                            else:
                                # Penalize if model predicts unprofitable
                                profitability_boost = (profitability_prob - 0.5) * CONFIG.get('profitability_boost_weight', 0.4)
                            
                            logger.info(f"Profitability Prediction - Prob: {profitability_prob:.3f}, "
                                       f"Profitable: {is_profitable}, Boost: {profitability_boost:.3f}")
                            append_log_safe(f"Profitability: {profitability_prob:.1%} (boost: {profitability_boost:+.2f})")
                except Exception as e:
                    logger.debug(f"Profitability prediction skipped: {e}")
            except Exception as e:
                logger.error(f"Profitability prediction error: {e}")
        
        # Add ML confidence boost
        confidence += ml_confidence_boost
        # Add profitability boost
        confidence += profitability_boost
        
        logger.info(f"Indicators - MACD: {btc_indicators['macd']}, {sol_indicators['macd']} | RSI: {btc_indicators['rsi']}, {sol_indicators['rsi']} | ADX: {btc_indicators.get('adx', 'N/A')}, {sol_indicators.get('adx', 'N/A')} | OBV: {btc_indicators['obv']}, {sol_indicators['obv']} | ML Boost: {ml_confidence_boost:.2f} | Profitability Boost: {profitability_boost:.2f} | Total Confidence: {confidence:.2f}")
        
        # Append to shared logs
        confidence_message = f"[{get_timestamp()}] Confidence: {confidence:.2f}"
        if ml_prediction:
            confidence_message += f" (ML: {ml_prediction['direction']} @ {ml_prediction['confidence']:.2f})"
        if profitability_prediction:
            confidence_message += f" (Profit: {profitability_prediction['probability']:.1%})"
        append_log_safe(confidence_message)

        if confidence < CONFIG['confidence_threshold']:
            logger.info(f"{get_timestamp()} Confidence too low. Skipping trade.")
            return balance_usdt, balance_sol, last_trade_time
        
        # Additional filter: if profitability model strongly predicts unprofitable, skip trade
        if CONFIG.get('profitability_prediction_enabled', False) and profitability_prediction:
            min_profitability_threshold = CONFIG.get('min_profitability_threshold', 0.3)
            if profitability_prediction['probability'] < min_profitability_threshold:
                logger.info(f"{get_timestamp()} Profitability prediction too low ({profitability_prediction['probability']:.1%}). Skipping trade.")
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
        
        # Log trade with context for future learning
        try:
            import json
            trade_log_entry = {
                'timestamp': get_timestamp(),
                'action': trade_action,
                'volume': volume,
                'price': sol_current_price,
                'balance_usdt': balance_usdt,
                'balance_sol': balance_sol,
                'confidence': confidence,
                'rsi_btc': btc_indicators.get('rsi'),
                'rsi_sol': sol_indicators.get('rsi'),
                'macd_btc': btc_indicators.get('macd', [0, 0])[0] if isinstance(btc_indicators.get('macd'), tuple) else 0,
                'macd_sol': sol_indicators.get('macd', [0, 0])[0] if isinstance(sol_indicators.get('macd'), tuple) else 0,
            }
            if ml_prediction:
                trade_log_entry['ml_direction'] = ml_prediction.get('direction')
                trade_log_entry['ml_confidence'] = ml_prediction.get('confidence')
            
            with open('trade_log.json', 'a') as f:
                json.dump(trade_log_entry, f)
                f.write('\n')
        except Exception as e:
            logger.debug(f"Error logging trade for learning: {e}")
        
        last_trade_time = now
        return balance_usdt, balance_sol, last_trade_time
    except Exception as e:
        logger.error(f"Error in handle_trade_with_fees: {e}")
        return balance_usdt, balance_sol, last_trade_time

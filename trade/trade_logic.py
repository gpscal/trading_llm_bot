import time
from config.config import CONFIG
from utils.utils import get_timestamp, log_and_print_status
from trade.volume_calculator import calculate_volume
from utils.logger import setup_logger
from utils.alerts import notify
from utils.shared_state import append_log_safe
# ML import is lazy-loaded to avoid circular dependencies

# Import notifiers and signal tracker
from utils.discord_notifier import get_discord_notifier
from utils.signal_tracker import get_signal_tracker

logger = setup_logger('trade_logic_logger', 'trade_logic.log')

def execute_trade(action, volume, price, balance_usdt, balance_coin, trade_fee):
    if action == 'buy':
        total_cost = volume * price * (1 + trade_fee)
        if balance_usdt < total_cost:
            volume = balance_usdt / (price * (1 + trade_fee))
            total_cost = volume * price * (1 + trade_fee)
        balance_usdt -= total_cost
        balance_coin += volume
    elif action == 'sell':
        if balance_coin < volume:
            volume = balance_coin
        total_revenue = volume * price * (1 - trade_fee)
        balance_usdt += total_revenue
        balance_coin -= volume
    return balance_usdt, balance_coin

async def handle_trade_with_fees(
    btc_current_price,
    sol_current_price,
    balance_usdt,
    balance_sol,
    last_trade_time,
    btc_indicators,
    sol_indicators,
    initial_sol_price,
    initial_total_usd,
    balance=None,
    selected_coin=None
):
    balance_coin_amount = balance_sol
    try:
        now = time.time()
        
        # EARLY EXIT: Check cooldown first before doing ANY expensive operations
        if now - last_trade_time < CONFIG['cooldown_period']:
            # Silently skip during cooldown (with 1-min poll, we only check once per minute anyway)
            time_remaining = CONFIG['cooldown_period'] - (now - last_trade_time)
            logger.debug(f"{get_timestamp()} Cooldown active ({time_remaining:.0f}s remaining)")
            return balance_usdt, balance_coin_amount, last_trade_time

        trade_coin = (selected_coin or (balance or {}).get('selected_coin') or CONFIG.get('default_coin', 'SOL')).upper()
        if trade_coin not in ('SOL', 'BTC'):
            logger.warning(f"{get_timestamp()} Unsupported trade coin {trade_coin}. Defaulting to SOL.")
            trade_coin = 'SOL'
        counter_coin = 'BTC' if trade_coin == 'SOL' else 'SOL'

        # Initialize balance structure if needed
        if balance is None:
            balance = {}
        balance.setdefault('coins', {})
        for coin in ('SOL', 'BTC'):
            balance['coins'].setdefault(coin, {
                'amount': 0.0,
                'price': 0.0,
                'indicators': {},
                'historical': [],
                'position_entry_price': None,
                'trailing_high_price': None,
            })
        balance['selected_coin'] = trade_coin

        primary_state = balance['coins'][trade_coin]
        secondary_state = balance['coins'][counter_coin]

        primary_price = sol_current_price if trade_coin == 'SOL' else btc_current_price
        secondary_price = btc_current_price if trade_coin == 'SOL' else sol_current_price

        primary_indicators = sol_indicators if trade_coin == 'SOL' else btc_indicators
        secondary_indicators = btc_indicators if trade_coin == 'SOL' else sol_indicators

        primary_momentum = (primary_indicators or {}).get('momentum', 0) or 0

        if btc_current_price is None or sol_current_price is None:
            logger.warning(f"{get_timestamp()} Missing price data (BTC={btc_current_price}, SOL={sol_current_price}). Skipping trade.")
            return balance_usdt, balance_coin_amount, last_trade_time

        if btc_current_price <= 0 or sol_current_price <= 0:
            logger.warning(f"{get_timestamp()} Invalid price data (BTC={btc_current_price}, SOL={sol_current_price}). Skipping trade.")
            return balance_usdt, balance_coin_amount, last_trade_time

        # --- Portfolio-level risk: max drawdown ---
        if balance is not None:
            # Update stored prices before risk calculations
            primary_state['price'] = primary_price
            secondary_state['price'] = secondary_price

            # Calculate total portfolio value across coins
            current_total_usd = balance_usdt
            for coin, state in balance['coins'].items():
                current_total_usd += state.get('amount', 0.0) * state.get('price', 0.0)
            # Initialize peak if missing
            peak_total_usd = balance.get('peak_total_usd', current_total_usd)
            if current_total_usd > peak_total_usd:
                peak_total_usd = current_total_usd
                balance['peak_total_usd'] = peak_total_usd
            max_drawdown_pct = CONFIG.get('max_drawdown_pct', 0) / 100.0
            if max_drawdown_pct > 0 and current_total_usd <= peak_total_usd * (1 - max_drawdown_pct) and balance_coin_amount > 0:
                # De-risk: liquidate current position
                trade_fee = CONFIG['trade_fee']
                volume_to_sell = balance_coin_amount
                pre_usdt, pre_coin = balance_usdt, balance_coin_amount
                balance_usdt, balance_coin_amount = execute_trade('sell', volume_to_sell, primary_price, balance_usdt, balance_coin_amount, trade_fee)
                primary_state['amount'] = balance_coin_amount
                msg = f"[{get_timestamp()}] Max drawdown hit. Liquidated {pre_coin:.6f} {trade_coin} at {primary_price:.2f}. USDT {pre_usdt:.2f} -> {balance_usdt:.2f}"
                logger.info(msg)
                append_log_safe(msg)
                notify(msg)
                if balance is not None:
                    primary_state['position_entry_price'] = None
                    primary_state['trailing_high_price'] = None
                return balance_usdt, balance_coin_amount, now

        btc_macd = btc_indicators.get('macd', (0, 0))
        sol_macd = sol_indicators.get('macd', (0, 0))
        btc_rsi = btc_indicators.get('rsi', 50)
        sol_rsi = sol_indicators.get('rsi', 50)
        btc_adx = btc_indicators.get('adx', 0)
        sol_adx = sol_indicators.get('adx', 0)
        btc_obv = btc_indicators.get('obv', 0)
        sol_obv = sol_indicators.get('obv', 0)

        macd_condition = (
            btc_macd[0] < CONFIG['macd_threshold']['btc'] and 
            sol_macd[0] < CONFIG['macd_threshold']['sol']
        )
        rsi_condition = (
            btc_rsi < CONFIG['rsi_threshold'] and 
            sol_rsi < CONFIG['rsi_threshold']
        )
        adx_condition = (
            btc_adx > CONFIG['adx_threshold'] and 
            sol_adx > CONFIG['adx_threshold']
        )
        obv_condition = (
            btc_obv > CONFIG['obv_threshold'] and 
            sol_obv > CONFIG['obv_threshold']
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
                    sol_historical = balance.get('coins', {}).get('SOL', {}).get('historical') if balance else None
                    btc_historical = balance.get('coins', {}).get('BTC', {}).get('historical') if balance else None
                    
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
        
        # Add LLM signal if enabled
        llm_boost = 0.0
        llm_signal = None
        if CONFIG.get('llm_enabled', False):
            try:
                from ml.llm_advisor import get_llm_advisor
                llm_advisor = get_llm_advisor(CONFIG)
                
                # Get historical data from balance if available
                sol_historical = balance.get('coins', {}).get('SOL', {}).get('historical') if balance else None
                btc_historical = balance.get('coins', {}).get('BTC', {}).get('historical') if balance else None
                
                # Get LLM signal (properly awaited in async context)
                try:
                    # Directly await the LLM call since we're now in an async function
                    llm_signal = await llm_advisor.get_trading_signal(
                        sol_current_price,
                        btc_current_price,
                        btc_indicators,
                        sol_indicators,
                        balance_usdt,
                        balance_coin_amount,
                        sol_historical,
                        btc_historical,
                        selected_coin=trade_coin  # Pass the selected trading coin
                    )
                    
                    if llm_signal is None:
                        logger.debug("LLM signal is None (may be throttled, cached, or failed - check llm_advisor.log)")
                    
                    if llm_signal:
                        llm_signal_str = llm_signal.get('signal', 'HOLD')
                        llm_confidence = llm_signal.get('confidence_score', 0.5)
                        is_cached_signal = llm_signal.get('is_cached', False)
                        
                        # Determine if LLM agrees with indicators
                        indicator_direction = 'up' if primary_momentum > 0 else 'down'
                        llm_direction = 'up' if llm_signal_str == 'BUY' else ('down' if llm_signal_str == 'SELL' else 'hold')
                        
                        if llm_direction == 'hold':
                            # LLM suggests holding - neutral/slight negative
                            llm_boost = 0.0
                        elif llm_direction == indicator_direction:
                            # LLM confirms indicators - positive boost
                            llm_boost = llm_confidence * CONFIG.get('llm_confidence_weight', 0.3)
                        else:
                            # LLM contradicts indicators - negative boost
                            llm_boost = -llm_confidence * CONFIG.get('llm_confidence_weight', 0.2)
                        
                        # Only log detailed info for fresh signals, not cached ones
                        if not is_cached_signal:
                            logger.info(f"LLM Signal: {llm_signal_str}, Confidence: {llm_confidence:.2f}, Boost: {llm_boost:.2f}")
                            append_log_safe(f"LLM: {llm_signal_str} (confidence: {llm_confidence:.2f}, boost: {llm_boost:+.2f})")
                        else:
                            logger.debug(f"LLM Signal (cached): {llm_signal_str}, Confidence: {llm_confidence:.2f}, Boost: {llm_boost:.2f}")
                except Exception as e:
                    logger.warning(f"LLM signal skipped due to exception: {e}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"LLM advisor error: {e}")
        
        # Add LLM boost
        confidence += llm_boost
        
        # Add Deep Analysis if enabled (comprehensive Claude AI + RAG analysis)
        deep_boost = 0.0
        deep_analysis = None
        if CONFIG.get('deep_analysis_enabled', False):
            try:
                from ml.deep_analyzer import get_deep_analyzer
                deep_analyzer = get_deep_analyzer(CONFIG)
                
                # Get deep analysis (cached, updates every 2-4 hours)
                # Convert coin symbol to proper format (BTC -> BTC/USD, SOL -> SOL/USD)
                analysis_symbol = f"{trade_coin}/USD"
                
                # Get historical data from balance if available
                coin_historical = balance.get('coins', {}).get(trade_coin, {}).get('historical') if balance else None
                
                try:
                    deep_analysis = await deep_analyzer.get_analysis(
                        symbol=analysis_symbol,
                        current_price=primary_price,
                        indicators=primary_indicators,
                        historical_data=coin_historical,
                        force_refresh=False  # Use cache if available
                    )
                    
                    if deep_analysis:
                        # Analyze consensus between fast LLM and deep analysis
                        deep_action = deep_analysis.recommended_action
                        deep_confidence = deep_analysis.confidence
                        deep_trend = deep_analysis.trend
                        
                        # Determine if deep analysis agrees with indicators
                        indicator_direction = 'up' if primary_momentum > 0 else 'down'
                        deep_direction = 'up' if deep_action == 'BUY' else ('down' if deep_action == 'SELL' else 'hold')
                        
                        # Calculate agreement between fast LLM and deep analysis
                        fast_llm_direction = 'hold'
                        if llm_signal:
                            llm_signal_str = llm_signal.get('signal', 'HOLD')
                            fast_llm_direction = 'up' if llm_signal_str == 'BUY' else ('down' if llm_signal_str == 'SELL' else 'hold')
                        
                        agreement_score = 0.0
                        if fast_llm_direction != 'hold' and deep_direction != 'hold':
                            if fast_llm_direction == deep_direction:
                                agreement_score = 1.0  # Perfect agreement
                            else:
                                agreement_score = -0.5  # Disagreement
                        
                        # Deep analysis boost calculation
                        if deep_direction == 'hold':
                            # Deep analysis suggests holding - slight negative
                            deep_boost = -0.1
                        elif deep_direction == indicator_direction:
                            # Deep analysis confirms indicators - strong positive
                            base_boost = deep_confidence * CONFIG.get('deep_analysis_confidence_weight', 0.35)
                            # Bonus if fast LLM also agrees
                            agreement_bonus = agreement_score * 0.15 if agreement_score > 0 else 0
                            deep_boost = base_boost + agreement_bonus
                        else:
                            # Deep analysis contradicts indicators - strong negative
                            deep_boost = -deep_confidence * CONFIG.get('deep_analysis_confidence_weight', 0.25)
                        
                        logger.info(
                            f"Deep Analysis: {deep_action}, Confidence: {deep_confidence:.2f}, "
                            f"Trend: {deep_trend}, Boost: {deep_boost:.2f}, "
                            f"Agreement with Fast LLM: {agreement_score:.2f}"
                        )
                        append_log_safe(
                            f"?? Deep: {deep_action} (conf: {deep_confidence:.2f}, "
                            f"trend: {deep_trend}, boost: {deep_boost:+.2f})"
                        )
                        
                        # Log key patterns and warnings
                        if deep_analysis.key_patterns:
                            logger.info(f"Deep Analysis Patterns: {', '.join(deep_analysis.key_patterns)}")
                        if deep_analysis.warnings:
                            logger.warning(f"Deep Analysis Warnings: {', '.join(deep_analysis.warnings)}")
                            for warning in deep_analysis.warnings:
                                append_log_safe(f"??  {warning}")
                    else:
                        logger.debug("Deep analysis returned None (may be throttled or cached)")
                        
                except Exception as e:
                    logger.warning(f"Deep analysis skipped due to exception: {e}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"Deep analyzer error: {e}")
        
        # Add deep analysis boost
        confidence += deep_boost
        
        logger.info(
            f"Indicators - BTC MACD: {btc_indicators.get('macd')}, SOL MACD: {sol_indicators.get('macd')} | "
            f"RSI BTC: {btc_indicators.get('rsi')}, SOL: {sol_indicators.get('rsi')} | "
            f"ADX BTC: {btc_indicators.get('adx')}, SOL: {sol_indicators.get('adx')} | "
            f"OBV BTC: {btc_indicators.get('obv')}, SOL: {sol_indicators.get('obv')} | "
            f"ML Boost: {ml_confidence_boost:.2f} | Profitability Boost: {profitability_boost:.2f} | "
            f"LLM Boost: {llm_boost:.2f} | Deep Boost: {deep_boost:.2f} | Total Confidence: {confidence:.2f}"
        )

        confidence_message = f"[{get_timestamp()}] Confidence: {confidence:.2f}"
        if ml_prediction:
            confidence_message += f" (ML: {ml_prediction['direction']} @ {ml_prediction['confidence']:.2f})"
        if profitability_prediction:
            confidence_message += f" (Profit: {profitability_prediction['probability']:.1%})"
        if llm_signal:
            confidence_message += f" (LLM: {llm_signal.get('signal', 'N/A')} @ {llm_signal.get('confidence_score', 0):.2f})"
        if deep_analysis:
            confidence_message += f" (Deep: {deep_analysis.recommended_action} @ {deep_analysis.confidence:.2f})"
        append_log_safe(confidence_message)

        if confidence < CONFIG['confidence_threshold']:
            logger.info(f"{get_timestamp()} Confidence too low. Skipping trade.")
            return balance_usdt, balance_coin_amount, last_trade_time

        if CONFIG.get('profitability_prediction_enabled', False) and profitability_prediction:
            min_profitability_threshold = CONFIG.get('min_profitability_threshold', 0.3)
            if profitability_prediction['probability'] < min_profitability_threshold:
                logger.info(f"{get_timestamp()} Profitability prediction too low ({profitability_prediction['probability']:.1%}). Skipping trade.")
                return balance_usdt, balance_coin_amount, last_trade_time

        if CONFIG.get('llm_enabled', False) and CONFIG.get('llm_final_authority', True):
            # Check if consensus mode is enabled (requires BOTH Fast LLM and Deep Analysis to agree)
            consensus_required = CONFIG.get('llm_consensus_required', False)
            
            if llm_signal:
                llm_signal_str = llm_signal.get('signal', 'HOLD')
                
                # Check if this is a fresh signal or cached
                is_cached = llm_signal.get('is_cached', False)
                
                # Only update signal tracking and check stability for FRESH signals
                signal_tracker = get_signal_tracker()
                
                if not is_cached:
                    # Fresh signal - update tracking and check stability
                    logger.debug(f"Fresh LLM signal received for {trade_coin}: {llm_signal_str}")
                    signal_changed, old_signal = signal_tracker.check_signal_change(trade_coin, llm_signal_str)
                    
                    # Check signal stability if required
                    if CONFIG.get('llm_signal_stability_required', False):
                        stability_count = CONFIG.get('llm_signal_stability_count', 2)
                        is_stable, stable_signal = signal_tracker.check_signal_stability(trade_coin, stability_count)
                        
                        if not is_stable:
                            msg = (
                                f"{get_timestamp()} Signal stability check failed for {trade_coin}. "
                                f"Need {stability_count} consecutive {llm_signal_str} signals. "
                                f"Skipping trade for safety."
                            )
                            logger.info(msg)
                            append_log_safe(f"⏳ STABILITY CHECK: Need {stability_count} consecutive signals for {trade_coin}")
                            
                            # Show recent signal history
                            recent_signals = signal_tracker.get_signal_history(trade_coin, count=stability_count)
                            if recent_signals:
                                signals_str = " → ".join([sig for sig, _ in recent_signals])
                                append_log_safe(f"   Recent signals: {signals_str}")
                            
                            return balance_usdt, balance_coin_amount, last_trade_time
                        else:
                            logger.info(f"✓ Signal stability confirmed for {trade_coin}: {stability_count} consecutive {stable_signal} signals")
                            append_log_safe(f"✓ STABILITY CHECK PASSED: {stability_count}x {stable_signal} for {trade_coin}")
                    
                    # Send signal change notifications if signal changed
                    if signal_changed and old_signal:
                        logger.info(f"Signal changed for {trade_coin}: {old_signal} → {llm_signal_str}")
                        # Send Discord notification
                        try:
                            import asyncio
                            discord_notifier = await get_discord_notifier()
                            await discord_notifier.send_signal_change_alert(
                                coin=trade_coin,
                                old_signal=old_signal,
                                new_signal=llm_signal_str,
                                price=primary_price,
                                confidence=confidence,
                                llm_signal=llm_signal
                            )
                            logger.info(f"Discord signal change alert sent for {trade_coin}")
                        except Exception as e:
                            logger.warning(f"Failed to send Discord signal change notification: {e}")
                else:
                    # Cached signal - just log, no stability check
                    logger.debug(f"Using cached LLM signal for {trade_coin}: {llm_signal_str}")
                
                if llm_signal_str == 'HOLD':
                    msg = f"{get_timestamp()} LLM Advisor says HOLD - vetoing trade (Confidence was: {confidence:.2f})"
                    logger.info(msg)
                    append_log_safe(f"?? LLM VETO: HOLD signal blocks trade for {trade_coin}")
                    return balance_usdt, balance_coin_amount, last_trade_time

                indicator_trade_direction = 'buy' if primary_momentum > 0 else 'sell'
                llm_direction = 'buy' if llm_signal_str == 'BUY' else 'sell'
                if indicator_trade_direction != llm_direction:
                    msg = (
                        f"{get_timestamp()} LLM Advisor disagrees with indicators - vetoing trade. "
                        f"LLM: {llm_signal_str}, Indicators: {indicator_trade_direction.upper()}"
                    )
                    logger.info(msg)
                    append_log_safe(f"?? LLM VETO: {llm_signal_str} contradicts indicators for {trade_coin}")
                    return balance_usdt, balance_coin_amount, last_trade_time

                # CONSENSUS MODE: Check if both Fast LLM and Deep Analysis agree
                if consensus_required:
                    if not deep_analysis:
                        msg = f"{get_timestamp()} Consensus mode: Deep Analysis unavailable - skipping trade"
                        logger.info(msg)
                        append_log_safe(f"⚠️ CONSENSUS: Deep Analysis missing, skipping {trade_coin}")
                        return balance_usdt, balance_coin_amount, last_trade_time
                    
                    deep_action = deep_analysis.recommended_action
                    
                    # Check if Fast LLM and Deep Analysis agree
                    if llm_signal_str != deep_action:
                        msg = (
                            f"{get_timestamp()} Consensus mode: Fast LLM ({llm_signal_str}) and "
                            f"Deep Analysis ({deep_action}) disagree - skipping trade"
                        )
                        logger.info(msg)
                        append_log_safe(f"⚠️ CONSENSUS FAILED: Fast={llm_signal_str}, Deep={deep_action} for {trade_coin}")
                        return balance_usdt, balance_coin_amount, last_trade_time
                    
                    # Both agree but both say HOLD
                    if llm_signal_str == 'HOLD':
                        msg = f"{get_timestamp()} Consensus mode: Both LLMs say HOLD - skipping trade"
                        logger.info(msg)
                        append_log_safe(f"✓ CONSENSUS: Both HOLD for {trade_coin}")
                        return balance_usdt, balance_coin_amount, last_trade_time
                    
                    # Both agree on BUY or SELL!
                    logger.info(
                        f"{get_timestamp()} ✓ CONSENSUS ACHIEVED: Both Fast LLM and Deep Analysis agree on {llm_signal_str} "
                        f"(Deep confidence: {deep_analysis.confidence:.2f})"
                    )
                    append_log_safe(
                        f"✓ CONSENSUS: Both {llm_signal_str} for {trade_coin} "
                        f"(Deep: {deep_analysis.confidence:.0%} confidence)"
                    )
                else:
                    # Non-consensus mode: Fast LLM approval is sufficient
                    logger.info(f"{get_timestamp()} ✅ LLM Advisor APPROVES trade: {llm_signal_str} on {trade_coin}")
                    append_log_safe(f"✅ LLM APPROVED: {llm_signal_str} {trade_coin}")
            else:
                # Fast LLM not available - check if deep analysis can make decision
                if not CONFIG.get('deep_analysis_enabled', False):
                    # No LLM signal and no deep analysis - skip trade
                    msg = f"{get_timestamp()} LLM enabled but no signal available - skipping trade for safety"
                    logger.info(msg)
                    append_log_safe(f"?? LLM: No signal, skipping trade for {trade_coin}")
                    return balance_usdt, balance_coin_amount, last_trade_time
                elif consensus_required:
                    # Consensus mode: BOTH required, Fast missing means no trade
                    msg = f"{get_timestamp()} Consensus mode: Fast LLM unavailable - skipping trade"
                    logger.info(msg)
                    append_log_safe(f"⚠️ CONSENSUS: Fast LLM missing, skipping {trade_coin}")
                    return balance_usdt, balance_coin_amount, last_trade_time
                elif not deep_analysis:
                    # Deep analysis enabled but also unavailable (throttled) - skip trade
                    msg = f"{get_timestamp()} Both Fast LLM and Deep Analysis unavailable - skipping trade for safety"
                    logger.info(msg)
                    append_log_safe(f"⚠️ Both LLMs throttled, skipping trade for {trade_coin}")
                    return balance_usdt, balance_coin_amount, last_trade_time
                else:
                    # Non-consensus mode: Deep analysis can make decision alone
                    logger.info(f"{get_timestamp()} Fast LLM unavailable (throttled), using Deep Analysis...")
                    append_log_safe(f"⚠️ Fast LLM throttled, using Deep Analysis for {trade_coin}")
        
        # Deep Analysis veto power (if enabled and high confidence)
        # Note: In consensus mode, this section is mostly redundant since consensus was already checked above
        if not consensus_required and CONFIG.get('deep_analysis_enabled', False) and CONFIG.get('deep_analysis_veto_power', True):
            if deep_analysis and deep_analysis.confidence >= 0.7:  # High confidence threshold
                deep_action = deep_analysis.recommended_action
                indicator_trade_direction = 'buy' if primary_momentum > 0 else 'sell'
                deep_direction = 'buy' if deep_action == 'BUY' else ('sell' if deep_action == 'SELL' else 'hold')
                
                if deep_action == 'HOLD':
                    msg = (
                        f"{get_timestamp()} Deep Analysis says HOLD with high confidence "
                        f"({deep_analysis.confidence:.2f}) - vetoing trade"
                    )
                    logger.info(msg)
                    append_log_safe(f"⚠️ DEEP VETO: HOLD (confidence: {deep_analysis.confidence:.0%})")
                    if deep_analysis.warnings:
                        append_log_safe(f"⚠️  Reasons: {'; '.join(deep_analysis.warnings[:2])}")
                    return balance_usdt, balance_coin_amount, last_trade_time
                
                if indicator_trade_direction != deep_direction:
                    msg = (
                        f"{get_timestamp()} Deep Analysis disagrees with indicators (confidence: {deep_analysis.confidence:.2f}) "
                        f"- vetoing trade. Deep: {deep_action}, Indicators: {indicator_trade_direction.upper()}"
                    )
                    logger.info(msg)
                    append_log_safe(f"⚠️ DEEP VETO: {deep_action} contradicts {indicator_trade_direction.upper()}")
                    return balance_usdt, balance_coin_amount, last_trade_time
                
                logger.info(f"{get_timestamp()} ✅ Deep Analysis APPROVES trade: {deep_action} (confidence: {deep_analysis.confidence:.2f})")
                append_log_safe(f"✅ DEEP APPROVED: {deep_action} {trade_coin} ({deep_analysis.trend})")
            elif deep_analysis:
                logger.info(f"{get_timestamp()} Deep Analysis present but confidence too low for veto ({deep_analysis.confidence:.2f})")

        trade_action = 'buy' if primary_momentum > 0 else 'sell'
        trade_fee = CONFIG['trade_fee']

        volume_limits = CONFIG.get('coin_volume_limits', {}).get(trade_coin, {})
        min_position_threshold = max(1e-6, volume_limits.get('min', CONFIG.get('min_volume', 0.001)) / 2)
        reentry_min_usdt = CONFIG.get('reentry_min_usdt', 5)

        if trade_action == 'sell' and balance_coin_amount <= min_position_threshold and balance_usdt >= reentry_min_usdt:
            logger.info(
                f"{get_timestamp()} Want to sell but no {trade_coin} ({balance_coin_amount:.6f}). "
                f"Overriding to buy to enter position (USDT: {balance_usdt:.2f}, min re-entry: {reentry_min_usdt})."
            )
            trade_action = 'buy'
            primary_momentum = max(primary_momentum, 1)
        elif trade_action == 'buy' and balance_usdt <= 0.01 and balance_coin_amount > 0:
            logger.info(
                f"{get_timestamp()} Want to buy but no USDT ({balance_usdt:.2f}). "
                f"Overriding to sell to free up capital ({trade_coin}: {balance_coin_amount:.6f})."
            )
            trade_action = 'sell'
            primary_momentum = min(primary_momentum, -1)

        logger.info(
            f"{get_timestamp()} Trade decision: {trade_coin} momentum={primary_momentum:.2f}, Action={trade_action}, "
            f"Balance: USDT={balance_usdt:.2f}, {trade_coin}={balance_coin_amount:.6f}"
        )

        if trade_action == 'buy':
            if balance_usdt <= 0:
                logger.info(f"{get_timestamp()} Cannot buy: insufficient USDT balance ({balance_usdt:.2f}). Need to sell first.")
                return balance_usdt, balance_coin_amount, last_trade_time
            volume = calculate_volume(primary_price, balance_usdt, CONFIG, trade_coin)
            max_affordable = balance_usdt / (primary_price * (1 + trade_fee))
            if max_affordable <= 0:
                logger.info(f"{get_timestamp()} Cannot buy: max affordable volume is non-positive ({max_affordable}).")
                return balance_usdt, balance_coin_amount, last_trade_time
            volume = min(volume, max_affordable)
            logger.info(f"{get_timestamp()} Buy volume calculated: {volume:.6f} {trade_coin} (from {balance_usdt:.2f} USDT)")
        else:
            if balance_coin_amount <= 0:
                logger.info(
                    f"{get_timestamp()} Cannot sell: insufficient {trade_coin} balance ({balance_coin_amount:.6f}). Need to buy first."
                )
                return balance_usdt, balance_coin_amount, last_trade_time
            coin_value_usd = balance_coin_amount * primary_price
            volume = calculate_volume(primary_price, coin_value_usd, CONFIG, trade_coin)
            volume = min(volume, balance_coin_amount)
            logger.info(
                f"{get_timestamp()} Sell volume calculated: {volume:.6f} {trade_coin} "
                f"(from {balance_coin_amount:.6f} {trade_coin} available)"
            )

        if volume <= 0:
            logger.info(f"{get_timestamp()} Volume too low to execute trade: {volume}. Transaction did not go through.")
            return balance_usdt, balance_coin_amount, last_trade_time

        if balance is not None and balance_coin_amount > 0:
            entry = primary_state.get('position_entry_price')
            trailing_high = primary_state.get('trailing_high_price', entry)
            if entry:
                trailing_high = max(trailing_high or entry, primary_price)
                primary_state['trailing_high_price'] = trailing_high
                if CONFIG.get('stop_loss_pct'):
                    if (entry - primary_price) / entry >= CONFIG['stop_loss_pct'] / 100.0:
                        sell_vol = balance_coin_amount
                        pre_coin = balance_coin_amount
                        balance_usdt, balance_coin_amount = execute_trade('sell', sell_vol, primary_price, balance_usdt, balance_coin_amount, trade_fee)
                        primary_state['amount'] = balance_coin_amount
                        msg = f"[{get_timestamp()}] Stop-loss triggered. Sold {pre_coin:.6f} {trade_coin} at {primary_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        primary_state['position_entry_price'] = None
                        primary_state['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_coin_amount, last_trade_time
                if CONFIG.get('base_take_profit_pct'):
                    if (primary_price - entry) / entry >= CONFIG['base_take_profit_pct'] / 100.0:
                        sell_vol = balance_coin_amount
                        pre_coin = balance_coin_amount
                        balance_usdt, balance_coin_amount = execute_trade('sell', sell_vol, primary_price, balance_usdt, balance_coin_amount, trade_fee)
                        primary_state['amount'] = balance_coin_amount
                        msg = f"[{get_timestamp()}] Take-profit triggered. Sold {pre_coin:.6f} {trade_coin} at {primary_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        primary_state['position_entry_price'] = None
                        primary_state['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_coin_amount, last_trade_time
                if CONFIG.get('trailing_stop_pct') and trailing_high:
                    if primary_price <= trailing_high * (1 - CONFIG['trailing_stop_pct'] / 100.0):
                        sell_vol = balance_coin_amount
                        pre_coin = balance_coin_amount
                        balance_usdt, balance_coin_amount = execute_trade('sell', sell_vol, primary_price, balance_usdt, balance_coin_amount, trade_fee)
                        primary_state['amount'] = balance_coin_amount
                        msg = f"[{get_timestamp()}] Trailing stop triggered. Sold {pre_coin:.6f} {trade_coin} at {primary_price:.2f}"
                        logger.info(msg)
                        append_log_safe(msg)
                        notify(msg)
                        primary_state['position_entry_price'] = None
                        primary_state['trailing_high_price'] = None
                        last_trade_time = now
                        return balance_usdt, balance_coin_amount, last_trade_time

        pre_balance_coin = balance_coin_amount
        balance_usdt, balance_coin_amount = execute_trade(trade_action, volume, primary_price, balance_usdt, balance_coin_amount, trade_fee)
        primary_state['amount'] = balance_coin_amount
        primary_state['price'] = primary_price
        if balance is not None and trade_action == 'buy' and pre_balance_coin == 0 and balance_coin_amount > 0:
            primary_state['position_entry_price'] = primary_price
            primary_state['trailing_high_price'] = primary_price
        
        # Send Discord notification for trade execution
        try:
            import asyncio
            discord_notifier = await get_discord_notifier()
            await discord_notifier.send_trade_execution_alert(
                coin=trade_coin,
                action=trade_action.upper(),
                amount=volume,
                price=primary_price,
                total_value=volume * primary_price,
                balance_usdt=balance_usdt,
                balance_coin=balance_coin_amount
            )
            logger.info(f"Discord trade execution alert sent for {trade_coin}")
        except Exception as e:
            logger.warning(f"Failed to send Discord trade notification: {e}")

        # Update total portfolio metrics
        current_total_usd = balance_usdt
        for state in balance['coins'].values():
            current_total_usd += state.get('amount', 0.0) * state.get('price', 0.0)
        total_gain_usd = current_total_usd - initial_total_usd

        log_and_print_status(balance, current_total_usd, total_gain_usd, coin=trade_coin, trade_action=trade_action, volume=volume, price=primary_price)

        try:
            import json

            trade_log_entry = {
                'timestamp': get_timestamp(),
                'coin': trade_coin,
                'action': trade_action,
                'volume': volume,
                'price': primary_price,
                'balance_usdt': balance_usdt,
                'balance_coin': balance_coin_amount,
                'confidence': confidence,
                'rsi_primary': primary_indicators.get('rsi'),
                'rsi_secondary': secondary_indicators.get('rsi'),
                'macd_primary': (primary_indicators.get('macd') or (0, 0))[0],
                'macd_secondary': (secondary_indicators.get('macd') or (0, 0))[0],
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
        balance['last_trade_time'] = last_trade_time
        return balance_usdt, balance_coin_amount, last_trade_time
    except Exception as e:
        logger.error(f"Error in handle_trade_with_fees: {e}")
        return balance_usdt, balance_coin_amount, last_trade_time

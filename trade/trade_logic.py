import time
import numpy as np
from config.config import CONFIG
from utils.utils import get_timestamp, log_trade, print_status
from trade.volume_calculator import calculate_volume

def handle_trade_with_fees(btc_current_price, sol_current_price, btc_previous_price, balance_usdt, balance_sol, last_trade_time, btc_indicators, sol_indicators):
    now = time.time()
    trade_fee = 0.003  # 0.3% trade fee

    # Implement a cooldown period (e.g., 60 seconds)
    if now - last_trade_time < CONFIG['cooldown_period']:
        print(f"{get_timestamp()} Cooldown period active. Skipping trade.")
        return {
            'balance_usdt': balance_usdt,
            'balance_sol': balance_sol,
            'btc_previous_price': btc_previous_price,
            'total_usd': balance_usdt + balance_sol * sol_current_price,
            'last_trade_time': last_trade_time,
            'btc_momentum': 0.0,
            'confidence': 0.0,
            'trade_action': None,
            'trade_volume': 0
        }

    btc_momentum = round(btc_current_price - btc_previous_price, 2)
    confidence = calculate_confidence(btc_indicators, sol_indicators, btc_momentum)

    # Increase the threshold for confidence to trigger a trade
    if confidence <= 0.5:
        print(f"{get_timestamp()} Confidence too low. Skipping trade.")
        return {
            'balance_usdt': balance_usdt,
            'balance_sol': balance_sol,
            'btc_previous_price': btc_previous_price,
            'total_usd': balance_usdt + balance_sol * sol_current_price,
            'last_trade_time': last_trade_time,
            'btc_momentum': 0.0,
            'confidence': confidence,
            'trade_action': None,
            'trade_volume': 0
        }

    trade_volume = calculate_volume(sol_current_price, balance_usdt, CONFIG)
    trade_action = None
    potential_profit = 0

    if btc_momentum > 0 and confidence > 0.5:
        trade_action = 'buy'
        potential_profit = (sol_current_price * trade_volume) * (1 - trade_fee)
    elif btc_momentum < 0 and confidence > 0.5:
        trade_action = 'sell'
        potential_profit = (sol_current_price * trade_volume) * (1 - trade_fee)

    if potential_profit < trade_fee * (sol_current_price * trade_volume):
        trade_action = None

    if trade_action == 'buy' and sol_current_price and balance_usdt >= trade_volume * sol_current_price:
        cost = trade_volume * sol_current_price
        fee = cost * trade_fee
        balance_usdt -= (cost + fee)
        balance_sol += trade_volume
        log_trade('buy', trade_volume, sol_current_price, balance_usdt, balance_sol)
        last_trade_time = now
    elif trade_action == 'sell' and sol_current_price and balance_sol >= trade_volume:
        revenue = trade_volume * sol_current_price
        fee = revenue * trade_fee
        balance_usdt += (revenue - fee)
        balance_sol -= trade_volume
        log_trade('sell', trade_volume, sol_current_price, balance_usdt, balance_sol)
        last_trade_time = now

    total_balance_usd = balance_usdt + balance_sol * sol_current_price
    take_profit_pct = calculate_take_profit_pct(confidence, CONFIG['base_take_profit_pct'])
    risk_action = None

    if confidence > 1.2:
        risk_action = 'take-profit'
    elif confidence == 0 and balance_sol == CONFIG['initial_balance_sol']:
        risk_action = None
    elif confidence < 0.5 and btc_momentum < 0:
        risk_action = 'stop-loss'

    # Evaluate risk actions independently
    if risk_action == 'stop-loss' and balance_sol > 0:
        actual_trade_volume = min(trade_volume, balance_sol)
        if actual_trade_volume >= CONFIG['min_volume']:
            revenue = actual_trade_volume * sol_current_price
            fee = revenue * trade_fee
            balance_sol -= actual_trade_volume
            balance_usdt += (revenue - fee)
            log_trade('stop-loss', actual_trade_volume, sol_current_price, balance_usdt, balance_sol)
            last_trade_time = now
        else:
            print(f"Not enough SOL to sell for stop-loss")
    elif risk_action == 'take-profit' and balance_sol > 0:
        actual_trade_volume = min(trade_volume, balance_sol)
        if actual_trade_volume >= CONFIG['min_volume']:
            revenue = actual_trade_volume * sol_current_price
            fee = revenue * trade_fee
            balance_sol -= actual_trade_volume
            balance_usdt += (revenue - fee)
            log_trade('take-profit', actual_trade_volume, sol_current_price, balance_usdt, balance_sol)
            last_trade_time = now
        else:
            print(f"Not enough SOL to sell for take-profit")

    return {
        'balance_usdt': balance_usdt,
        'balance_sol': balance_sol,
        'btc_previous_price': btc_current_price,
        'total_usd': total_balance_usd,
        'last_trade_time': now,
        'btc_momentum': btc_momentum,
        'confidence': confidence,
        'trade_action': trade_action,
        'trade_volume': trade_volume
    }

def calculate_confidence(btc_indicators, sol_indicators, btc_momentum):
    confidence = 0.0
    
    indicator_weights = {
        'macd': 0.5,  # MACD is a strong momentum indicator
        'rsi': 0.3,  # RSI helps identify overbought/oversold conditions
        'moving_avg': 0.3,  # Moving average is useful for trend identification
        'stochastic_oscillator': 0.2,  # Stochastic oscillator confirms momentum changes
        'atr': 0.2,  # ATR is useful for measuring market volatility
        'btc_momentum': 0.3  # BTC momentum provides direct momentum insight
    }
    
    macd_condition = (btc_indicators['macd'][0] < btc_indicators['macd'][1]) and (sol_indicators['macd'][0] < sol_indicators['macd'][1])
    rsi_condition = (btc_indicators['rsi'] < 30) and (sol_indicators['rsi'] < 30)
    moving_avg_condition = (btc_indicators['moving_avg'] < btc_indicators['macd'][0]) and (sol_indicators['moving_avg'] < sol_indicators['macd'][0])
    stochastic_oscillator_condition = (btc_indicators['stochastic_oscillator'] < 20) and (sol_indicators['stochastic_oscillator'] < 20)
    atr_condition = (np.mean(btc_indicators['atr']) > 1.5 * np.median(btc_indicators['atr'])) and (np.mean(sol_indicators['atr']) > 1.5 * np.median(sol_indicators['atr']))
    btc_momentum_condition = btc_momentum > 0

    if macd_condition:
        confidence += indicator_weights['macd']
    if rsi_condition:
        confidence += indicator_weights['rsi']
    if moving_avg_condition:
        confidence += indicator_weights['moving_avg']
    if stochastic_oscillator_condition:
        confidence += indicator_weights['stochastic_oscillator']
    if atr_condition:
        confidence += indicator_weights['atr']
    if btc_momentum_condition:
        confidence += indicator_weights['btc_momentum']

    print(f"MACD Condition: {macd_condition} (BTC: {btc_indicators['macd'][0]} < {btc_indicators['macd'][1]}, SOL: {sol_indicators['macd'][0]} < {sol_indicators['macd'][1]})")
    print(f"RSI Condition: {rsi_condition} (BTC: {btc_indicators['rsi']} < 30, SOL: {sol_indicators['rsi']} < 30)")
    print(f"Moving Avg Condition: {moving_avg_condition} (BTC: {btc_indicators['moving_avg']} < {btc_indicators['macd'][0]}, SOL: {sol_indicators['moving_avg']} < {sol_indicators['macd'][0]})")
    print(f"Stochastic Oscillator Condition: {stochastic_oscillator_condition} (BTC: {btc_indicators['stochastic_oscillator']} < 20, SOL: {sol_indicators['stochastic_oscillator']} < 20)")
    print(f"ATR Condition: {atr_condition} (BTC ATR Mean: {np.mean(btc_indicators['atr'])}, Median: {np.median(btc_indicators['atr'])}, Std: {np.std(btc_indicators['atr'])}, "
          f"SOL ATR Mean: {np.mean(sol_indicators['atr'])}, Median: {np.median(sol_indicators['atr'])}, Std: {np.std(sol_indicators['atr'])})")
    print(f"BTC Momentum Condition: {btc_momentum_condition} (BTC Momentum: {btc_momentum})")
    print(f"Calculated Confidence: {confidence}")

    return confidence

def calculate_take_profit_pct(confidence, base_take_profit_pct):
    return base_take_profit_pct * confidence

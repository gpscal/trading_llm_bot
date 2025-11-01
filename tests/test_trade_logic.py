"""Unit tests for trade logic and decision making."""

import pytest
import time
from trade.trade_logic import execute_trade, handle_trade_with_fees
from config.config import CONFIG


class TestExecuteTrade:
    def test_buy_with_sufficient_balance(self):
        """Test buying SOL with sufficient USDT balance."""
        usdt = 1000.0
        sol = 0.0
        price = 100.0
        volume = 5.0
        fee = 0.003
        
        new_usdt, new_sol = execute_trade('buy', volume, price, usdt, sol, fee)
        
        total_cost = volume * price * (1 + fee)
        assert new_usdt == pytest.approx(usdt - total_cost, abs=0.01)
        assert new_sol == pytest.approx(sol + volume, abs=0.0001)
    
    def test_buy_insufficient_balance(self):
        """Test buying adjusts volume if USDT balance is insufficient."""
        usdt = 100.0  # Only enough for ~0.83 SOL at 100 price + fee
        sol = 0.0
        price = 100.0
        volume = 5.0  # Too much
        fee = 0.003
        
        new_usdt, new_sol = execute_trade('buy', volume, price, usdt, sol, fee)
        
        # Should use all USDT
        assert new_usdt == pytest.approx(0.0, abs=0.01)
        assert new_sol > 0
        assert new_sol < volume  # Adjusted down
    
    def test_sell_with_sufficient_balance(self):
        """Test selling SOL with sufficient balance."""
        usdt = 0.0
        sol = 10.0
        price = 100.0
        volume = 5.0
        fee = 0.003
        
        new_usdt, new_sol = execute_trade('sell', volume, price, usdt, sol, fee)
        
        total_revenue = volume * price * (1 - fee)
        assert new_usdt == pytest.approx(usdt + total_revenue, abs=0.01)
        assert new_sol == pytest.approx(sol - volume, abs=0.0001)
    
    def test_sell_insufficient_balance(self):
        """Test selling adjusts volume if SOL balance is insufficient."""
        usdt = 0.0
        sol = 2.0
        price = 100.0
        volume = 5.0  # Too much
        fee = 0.003
        
        new_usdt, new_sol = execute_trade('sell', volume, price, usdt, sol, fee)
        
        # Should sell all SOL
        assert new_sol == pytest.approx(0.0, abs=0.0001)
        assert new_usdt > 0
        assert new_usdt < volume * price  # After fees


class TestHandleTradeWithFees:
    def test_cooldown_period(self):
        """Test that trades are skipped during cooldown period."""
        now = time.time()
        last_trade = now - 0.5  # 0.5 seconds ago, cooldown is typically 1s
        
        btc_indicators = {'macd': (-100, 0), 'rsi': 30, 'momentum': -200}
        sol_indicators = {'macd': (-1, 0), 'rsi': 30, 'momentum': -20}
        
        usdt, sol, new_time = handle_trade_with_fees(
            btc_price=50000.0,
            sol_current_price=100.0,
            balance_usdt=1000.0,
            balance_sol=0.0,
            last_trade_time=last_trade,
            btc_indicators=btc_indicators,
            sol_indicators=sol_indicators,
            initial_sol_price=100.0,
            initial_total_usd=1000.0,
            balance=None
        )
        
        # Should return unchanged balance (no trade due to cooldown)
        assert usdt == 1000.0
        assert sol == 0.0
        assert new_time == last_trade  # Unchanged
    
    def test_low_confidence_skips_trade(self):
        """Test that trades are skipped when confidence is too low."""
        now = time.time()
        last_trade = now - 10.0  # Past cooldown
        
        # Indicators that don't meet thresholds -> low confidence
        btc_indicators = {'macd': (-10, 0), 'rsi': 50, 'momentum': -10, 'adx': 0.1, 'obv': 10}
        sol_indicators = {'macd': (-0.1, 0), 'rsi': 50, 'momentum': -1, 'adx': 0.1, 'obv': 10}
        
        usdt, sol, new_time = handle_trade_with_fees(
            btc_price=50000.0,
            sol_current_price=100.0,
            balance_usdt=1000.0,
            balance_sol=0.0,
            last_trade_time=last_trade,
            btc_indicators=btc_indicators,
            sol_indicators=sol_indicators,
            initial_sol_price=100.0,
            initial_total_usd=1000.0,
            balance=None
        )
        
        # Should return unchanged balance (confidence too low)
        assert usdt == 1000.0
        assert sol == 0.0
    
    def test_high_confidence_executes_trade(self):
        """Test that trades execute when confidence threshold is met."""
        now = time.time()
        last_trade = now - 10.0  # Past cooldown
        
        # Indicators that meet thresholds -> high confidence
        btc_indicators = {
            'macd': (-100, 0),  # Below threshold
            'rsi': 30,  # Below threshold
            'momentum': 200,  # Positive momentum -> buy
            'adx': 20.0,  # Above threshold
            'obv': 5000.0  # Above threshold
        }
        sol_indicators = {
            'macd': (-1, 0),  # Below threshold
            'rsi': 30,  # Below threshold
            'momentum': 20,  # Positive momentum -> buy
            'adx': 20.0,  # Above threshold
            'obv': 5000.0  # Above threshold
        }
        
        usdt, sol, new_time = handle_trade_with_fees(
            btc_price=50000.0,
            sol_current_price=100.0,
            balance_usdt=1000.0,
            balance_sol=0.0,
            last_trade_time=last_trade,
            btc_indicators=btc_indicators,
            sol_indicators=sol_indicators,
            initial_sol_price=100.0,
            initial_total_usd=1000.0,
            balance={}
        )
        
        # Should execute buy trade (momentum > 0)
        assert new_time > last_trade
        # Balance should change
        assert sol > 0 or usdt < 1000.0

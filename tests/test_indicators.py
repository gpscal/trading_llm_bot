"""Unit tests for technical indicator calculations."""

import pytest
import numpy as np
from strategies.indicators import calculate_indicators
from strategies.indicators.moving_average import calculate_moving_average
from strategies.indicators.rsi import calculate_rsi
from strategies.indicators.macd import calculate_macd


def generate_ohlc_data(prices: list, volumes: list = None) -> list:
    """Generate mock OHLC data from price list.
    
    Format: [time, open, high, low, close, volume, ...]
    """
    if volumes is None:
        volumes = [1000.0] * len(prices)
    
    return [
        [0, p, p * 1.01, p * 0.99, p, volumes[i]] 
        for i, p in enumerate(prices)
    ]


class TestMovingAverage:
    def test_simple_ma(self):
        """Test moving average calculation with simple data."""
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        ohlc = generate_ohlc_data(prices)
        ma = calculate_moving_average(ohlc, period=3)
        # Last 3: 102, 103, 104 -> avg = 103
        assert ma == pytest.approx(103.0, abs=0.01)
    
    def test_ma_insufficient_data(self):
        """Test MA with insufficient data points."""
        prices = [100.0, 101.0]
        ohlc = generate_ohlc_data(prices)
        ma = calculate_moving_average(ohlc, period=5)
        assert ma is None


class TestRSI:
    def test_rsi_upward_trend(self):
        """Test RSI with upward trending prices."""
        prices = [100.0] * 10 + [101.0] * 5  # 10 flat, then 5 up
        ohlc = generate_ohlc_data(prices)
        rsi = calculate_rsi(ohlc, period=14)
        # RSI should be above 50 for upward trend
        assert rsi is not None
        assert rsi >= 50.0
        assert rsi <= 100.0
    
    def test_rsi_downward_trend(self):
        """Test RSI with downward trending prices."""
        prices = [100.0] * 10 + [99.0] * 5  # 10 flat, then 5 down
        ohlc = generate_ohlc_data(prices)
        rsi = calculate_rsi(ohlc, period=14)
        # RSI should be below 50 for downward trend
        assert rsi is not None
        assert rsi <= 50.0
        assert rsi >= 0.0


class TestMACD:
    def test_macd_calculation(self):
        """Test MACD returns tuple of (macd, signal)."""
        prices = [100.0 + i * 0.5 for i in range(30)]  # Upward trend
        ohlc = generate_ohlc_data(prices)
        macd_result = calculate_macd(ohlc, fast_period=12, slow_period=26, signal_period=9)
        assert macd_result is not None
        macd, signal = macd_result
        assert isinstance(macd, (int, float))
        assert isinstance(signal, (int, float))


class TestCalculateIndicators:
    def test_calculate_indicators_returns_dicts(self):
        """Test that calculate_indicators returns proper Python dicts."""
        btc_prices = [50000.0 + i * 100 for i in range(60)]
        sol_prices = [100.0 + i * 0.5 for i in range(60)]
        btc_ohlc = generate_ohlc_data(btc_prices)
        sol_ohlc = generate_ohlc_data(sol_prices)
        
        btc_ind, sol_ind = calculate_indicators(btc_ohlc, sol_ohlc)
        
        # Verify structure
        assert isinstance(btc_ind, dict)
        assert isinstance(sol_ind, dict)
        
        # Verify expected keys
        expected_keys = ['moving_avg', 'bollinger_bands', 'macd', 'rsi', 'atr',
                        'correlation', 'stochastic_oscillator', 'momentum', 'adx', 'obv']
        for key in expected_keys:
            assert key in btc_ind
            assert key in sol_ind
    
    def test_indicator_values_are_python_types(self):
        """Test that all indicator values are plain Python types (not numpy)."""
        btc_prices = [50000.0 + i * 100 for i in range(60)]
        sol_prices = [100.0 + i * 0.5 for i in range(60)]
        btc_ohlc = generate_ohlc_data(btc_prices)
        sol_ohlc = generate_ohlc_data(sol_prices)
        
        btc_ind, sol_ind = calculate_indicators(btc_ohlc, sol_ohlc)
        
        def check_python_type(val):
            """Recursively check value is a Python type, not numpy."""
            if val is None:
                return
            assert not isinstance(val, (np.ndarray, np.integer, np.floating, np.bool_))
            if isinstance(val, (list, tuple)):
                for v in val:
                    check_python_type(v)
            elif isinstance(val, dict):
                for v in val.values():
                    check_python_type(v)
        
        check_python_type(btc_ind)
        check_python_type(sol_ind)

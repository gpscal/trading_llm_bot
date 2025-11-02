"""
Train ML model from trading outcomes instead of just market data.

This creates a supervised learning dataset where:
- Input: Market features at trade time
- Output: Whether the trade was profitable (binary classification)
"""

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import json
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Tuple
import logging
from ml.data_collector import extract_features
from ml.price_predictor import LSTMPredictor
from ml.trade_learner import TradeHistoryAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('train_from_outcomes')


def load_trade_history_with_outcomes(trade_log_path: str = 'trade_log.json') -> List[Dict]:
    """Load trades and calculate their outcomes."""
    analyzer = TradeHistoryAnalyzer(trade_log_path)
    trades = analyzer.load_trade_history()
    
    if len(trades) < 50:
        logger.warning(f"Need at least 50 trades for training, found {len(trades)}")
        return []
    
    # Match buy/sell pairs to calculate outcomes
    buy_trades = [t for t in trades if t.get('action') == 'buy']
    sell_trades = [t for t in trades if t.get('action') == 'sell']
    pairs = analyzer._match_trade_pairs(buy_trades, sell_trades)
    
    # Enrich trades with outcome information
    enriched_trades = []
    for pair in pairs:
        buy = pair['buy']
        sell = pair['sell']
        
        profit_pct = analyzer._calculate_profit(pair)
        is_profitable = profit_pct > 0.5  # Account for fees
        
        enriched_trades.append({
            'trade': buy,
            'outcome': 1 if is_profitable else 0,
            'profit_pct': profit_pct,
            'entry_price': buy.get('price'),
            'exit_price': sell.get('price'),
        })
    
    logger.info(f"Loaded {len(enriched_trades)} trades with outcomes")
    logger.info(f"Profitable: {sum(1 for t in enriched_trades if t['outcome'] == 1)}, "
                f"Unprofitable: {sum(1 for t in enriched_trades if t['outcome'] == 0)}")
    
    return enriched_trades


def create_training_data_from_trades(enriched_trades: List[Dict], 
                                     historical_data: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create training dataset from trade outcomes.
    
    Args:
        enriched_trades: List of trades with outcomes
        historical_data: Dictionary mapping timestamps to OHLCV data
    
    Returns:
        X: Feature sequences (samples, sequence_length, features)
        y: Binary labels (1=profitable, 0=unprofitable)
    """
    X_list = []
    y_list = []
    
    for trade_data in enriched_trades:
        trade = trade_data['trade']
        timestamp = trade.get('timestamp', '')
        outcome = trade_data['outcome']
        
        # Get historical data around trade time
        # In production, you'd fetch this from your data store
        # For now, we'll need the historical data passed in
        
        # Extract features at trade time
        # This is simplified - in production, maintain feature cache
        try:
            # Assume historical_data contains OHLCV data
            # Extract 60 candles before trade
            features = None  # Would extract from historical_data
            
            if features is not None:
                X_list.append(features)
                y_list.append(outcome)
        except Exception as e:
            logger.debug(f"Skipping trade at {timestamp}: {e}")
    
    if len(X_list) == 0:
        logger.error("No valid training data extracted")
        return None, None
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    logger.info(f"Created training dataset: {X.shape}, labels: {y.shape}")
    return X, y


def train_profitability_model():
    """Train model to predict trade profitability."""
    # Load trade history
    enriched_trades = load_trade_history_with_outcomes()
    
    if len(enriched_trades) < 50:
        logger.error("Not enough trades for training. Need at least 50 trades.")
        logger.info("Run simulations or live trading to generate trade history first.")
        return
    
    # Create training data
    # Note: This requires historical OHLCV data at trade times
    # In production, maintain a database of historical features
    X, y = create_training_data_from_trades(enriched_trades, {})
    
    if X is None:
        logger.warning("Could not create training data. Historical features not available.")
        logger.info("This feature requires maintaining historical feature cache.")
        return
    
    # Train model (similar to train_model.py)
    # ... training code here ...
    
    logger.info("Training complete!")


if __name__ == '__main__':
    train_profitability_model()

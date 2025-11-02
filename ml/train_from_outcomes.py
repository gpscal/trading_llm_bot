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
from typing import List, Dict, Tuple, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from ml.data_collector import extract_features
from ml.trade_learner import TradeHistoryAnalyzer
from api.kraken import get_historical_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('train_from_outcomes')


class ProfitabilityPredictor(nn.Module):
    """
    Binary classifier to predict if a trade will be profitable.
    
    Uses LSTM to process sequence of market features and outputs
    probability that the trade will be profitable.
    """
    
    def __init__(self, input_size=20, hidden_size=64, num_layers=2, dropout=0.2):
        super(ProfitabilityPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        # Binary classification output (profitable or not)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output probability
        )
        
    def forward(self, x):
        # x shape: (batch, sequence_length, features)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Attention mechanism
        attention_weights = self.attention(lstm_out)  # (batch, seq_len, 1)
        attention_weights = torch.softmax(attention_weights, dim=1)
        attended = torch.sum(attention_weights * lstm_out, dim=1)  # (batch, hidden_size)
        
        # Binary classification
        output = self.fc(attended)
        return output.squeeze(-1)  # (batch,)


def load_trade_history_with_outcomes(trade_log_path: str = 'trade_log.json') -> List[Dict]:
    """Load trades and calculate their outcomes."""
    analyzer = TradeHistoryAnalyzer(trade_log_path)
    trades = analyzer.load_trade_history()
    
    if len(trades) < 10:
        logger.warning(f"Need at least 10 trades for training, found {len(trades)}")
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
        # Consider a trade profitable if profit > 0.5% (accounting for fees)
        is_profitable = profit_pct > 0.5
        
        enriched_trades.append({
            'trade': buy,
            'outcome': 1 if is_profitable else 0,
            'profit_pct': profit_pct,
            'entry_price': buy.get('price'),
            'exit_price': sell.get('price'),
            'timestamp': buy.get('timestamp'),
        })
    
    logger.info(f"Loaded {len(enriched_trades)} trades with outcomes")
    profitable_count = sum(1 for t in enriched_trades if t['outcome'] == 1)
    logger.info(f"Profitable: {profitable_count}, "
                f"Unprofitable: {len(enriched_trades) - profitable_count} "
                f"({profitable_count/len(enriched_trades)*100:.1f}% profitable)")
    
    return enriched_trades


async def fetch_historical_data_for_trades(
    enriched_trades: List[Dict],
    pair: str = 'SOLUSDT',
    interval_minutes: int = 60
) -> Tuple[Optional[List], Optional[List]]:
    """
    Fetch historical OHLCV data covering all trade timestamps.
    
    Returns:
        sol_ohlc: SOL historical data
        btc_ohlc: BTC historical data (for cross-asset features)
    """
    logger.info(f"Fetching historical data for {len(enriched_trades)} trades...")
    
    # Get date range from trades
    timestamps = [t['timestamp'] for t in enriched_trades]
    if not timestamps:
        return None, None
    
    try:
        # Parse earliest and latest timestamps
        earliest = min(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamps)
        latest = max(datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamps)
        
        # Fetch enough data to cover all trades (at least 7 days before earliest)
        logger.info(f"Trades span from {earliest} to {latest}")
        logger.info(f"Fetching historical data (interval={interval_minutes} minutes)...")
        
        # Fetch SOL data
        sol_ohlc = await get_historical_data(pair, interval_minutes)
        if not sol_ohlc or len(sol_ohlc) < 100:
            logger.warning(f"Insufficient SOL data: {len(sol_ohlc) if sol_ohlc else 0} candles")
            # Try to fetch BTC data anyway for cross-asset features
            btc_ohlc = await get_historical_data('XXBTZUSD', interval_minutes)
            return sol_ohlc, btc_ohlc
        
        logger.info(f"Fetched {len(sol_ohlc)} SOL candles")
        
        # Fetch BTC data for cross-asset features
        btc_ohlc = await get_historical_data('XXBTZUSD', interval_minutes)
        if btc_ohlc:
            logger.info(f"Fetched {len(btc_ohlc)} BTC candles")
        else:
            logger.warning("Could not fetch BTC data, using SOL data as fallback")
            
        return sol_ohlc, btc_ohlc
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return None, None


def extract_features_for_trade(
    trade_timestamp: str,
    sol_ohlc: List,
    btc_ohlc: Optional[List] = None,
    lookback_candles: int = 60
) -> Optional[np.ndarray]:
    """
    Extract features for a specific trade timestamp.
    
    Args:
        trade_timestamp: Trade timestamp string
        sol_ohlc: SOL OHLCV data (list of candles)
        btc_ohlc: BTC OHLCV data (optional)
        lookback_candles: Number of candles to use before trade
        
    Returns:
        Feature sequence of shape (lookback_candles, num_features) or None
    """
    try:
        # Parse trade timestamp
        trade_time = datetime.strptime(trade_timestamp, '%Y-%m-%d %H:%M:%S')
        
        # Kraken OHLC format: [timestamp, open, high, low, close, volume, ...]
        # Candles are typically sorted (newest or oldest first, check by comparing first/last)
        # For safety, we'll handle both cases
        
        # First, try to find candles matching trade time
        # If we can't match exactly, use the most recent N candles as fallback
        relevant_candles = []
        best_match_idx = -1
        min_time_diff = float('inf')
        
        # Check if candles are in reverse order (newest first - Kraken default)
        # Check first few candles to determine order
        is_reverse_order = False
        if len(sol_ohlc) > 1:
            try:
                first_time = datetime.fromtimestamp(float(sol_ohlc[0][0]))
                last_time = datetime.fromtimestamp(float(sol_ohlc[-1][0]))
                is_reverse_order = first_time > last_time
            except (ValueError, OverflowError):
                is_reverse_order = False  # Default assumption
        
        # Find the candle closest to trade time
        for idx, candle in enumerate(sol_ohlc):
            if len(candle) < 5:
                continue
            try:
                candle_time = datetime.fromtimestamp(float(candle[0]))
                time_diff = abs((candle_time - trade_time).total_seconds())
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_match_idx = idx
            except (ValueError, OverflowError):
                continue
        
        # If we found a match within 2 hours, use it
        if best_match_idx >= 0 and min_time_diff < 7200:  # 2 hours
            if is_reverse_order:
                # Newest first: get candles from index 0 to best_match_idx
                end_idx = min(best_match_idx + 1, len(sol_ohlc))
                relevant_candles = sol_ohlc[:end_idx]
            else:
                # Oldest first: get candles from 0 to best_match_idx
                relevant_candles = sol_ohlc[:best_match_idx + 1]
        else:
            # Fallback: use most recent N candles
            relevant_candles = sol_ohlc[:lookback_candles + 20]
        
        # Reverse if needed to get chronological order (oldest to newest)
        if is_reverse_order:
            relevant_candles = list(reversed(relevant_candles))
        
        # Need at least lookback_candles
        if len(relevant_candles) < lookback_candles:
            logger.debug(f"Not enough candles for trade at {trade_timestamp}: {len(relevant_candles)}")
            return None
        
        # Use the last lookback_candles (most recent before trade)
        candles_for_features = relevant_candles[-lookback_candles:]
        
        # Extract features using existing pipeline
        btc_relevant = None
        if btc_ohlc and len(btc_ohlc) >= lookback_candles:
            # Use same approach for BTC
            if is_reverse_order:
                btc_relevant = list(reversed(btc_ohlc[:lookback_candles + 20]))[-lookback_candles:]
            else:
                btc_relevant = btc_ohlc[:lookback_candles + 20][-lookback_candles:]
        
        # Extract features
        features = extract_features(candles_for_features, btc_relevant if btc_relevant else None)
        
        if features is None or len(features) < lookback_candles:
            logger.debug(f"Feature extraction failed for trade at {trade_timestamp}")
            return None
        
        # Return last lookback_candles (in case we got more)
        return features[-lookback_candles:]
        
    except Exception as e:
        logger.debug(f"Error extracting features for trade at {trade_timestamp}: {e}")
        return None


async def create_training_data_from_trades(
    enriched_trades: List[Dict],
    sol_ohlc: Optional[List],
    btc_ohlc: Optional[List]
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Create training dataset from trade outcomes.
    
    Args:
        enriched_trades: List of trades with outcomes
        sol_ohlc: SOL historical OHLCV data
        btc_ohlc: BTC historical OHLCV data (optional)
    
    Returns:
        X: Feature sequences (samples, sequence_length, features)
        y: Binary labels (1=profitable, 0=unprofitable)
    """
    X_list = []
    y_list = []
    
    if not sol_ohlc or len(sol_ohlc) < 60:
        logger.error("Insufficient historical data")
        return None, None
    
    logger.info(f"Extracting features for {len(enriched_trades)} trades...")
    
    successful = 0
    for i, trade_data in enumerate(enriched_trades):
        trade = trade_data['trade']
        timestamp = trade_data.get('timestamp', trade.get('timestamp', ''))
        outcome = trade_data['outcome']
        
        # Extract features at trade time
        features = extract_features_for_trade(timestamp, sol_ohlc, btc_ohlc)
        
        if features is not None and features.shape[0] >= 60:
            X_list.append(features)
            y_list.append(outcome)
            successful += 1
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i+1}/{len(enriched_trades)} trades, {successful} successful")
    
    if len(X_list) == 0:
        logger.error("No valid training data extracted")
        return None, None
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    logger.info(f"Created training dataset: {X.shape}, labels: {y.shape}")
    logger.info(f"Class distribution - Profitable: {np.sum(y==1)}, Unprofitable: {np.sum(y==0)}")
    
    return X, y


def split_data(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.8):
    """Split data into train and validation sets."""
    split_idx = int(len(X) * train_ratio)
    indices = np.random.permutation(len(X))
    train_indices = indices[:split_idx]
    val_indices = indices[split_idx:]
    
    X_train, X_val = X[train_indices], X[val_indices]
    y_train, y_val = y[train_indices], y[val_indices]
    
    return X_train, X_val, y_train, y_val


def train_profitability_model(
    model: nn.Module,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 50,
    batch_size: int = 16,
    learning_rate: float = 0.001,
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
) -> nn.Module:
    """
    Train the profitability prediction model.
    """
    model = model.to(device)
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train).to(device)
    y_train_t = torch.FloatTensor(y_train).to(device)
    X_val_t = torch.FloatTensor(X_val).to(device)
    y_val_t = torch.FloatTensor(y_val).to(device)
    
    # Loss and optimizer
    criterion = nn.BCELoss()  # Binary cross-entropy for binary classification
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    patience = 10
    
    logger.info(f"Training on {device} with {len(X_train)} samples...")
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        
        # Batch training
        for i in range(0, len(X_train_t), batch_size):
            batch_X = X_train_t[i:i+batch_size]
            batch_y = y_train_t[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            
            loss = criterion(outputs, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            train_loss += loss.item()
            # Predictions (threshold at 0.5)
            pred = (outputs > 0.5).float()
            train_correct += (pred == batch_y).sum().item()
        
        train_acc = train_correct / len(X_train_t)
        avg_train_loss = train_loss / (len(X_train_t) // batch_size + 1)
        
        # Validation
        model.eval()
        val_loss = 0
        val_correct = 0
        
        with torch.no_grad():
            for i in range(0, len(X_val_t), batch_size):
                batch_X = X_val_t[i:i+batch_size]
                batch_y = y_val_t[i:i+batch_size]
                
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                
                val_loss += loss.item()
                pred = (outputs > 0.5).float()
                val_correct += (pred == batch_y).sum().item()
        
        val_acc = val_correct / len(X_val_t)
        avg_val_loss = val_loss / (len(X_val_t) // batch_size + 1)
        
        scheduler.step(avg_val_loss)
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), 'models/profitability_predictor_best.pth')
        else:
            patience_counter += 1
        
        logger.info(f"Epoch {epoch+1}/{epochs} - "
                     f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                     f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch+1}")
            break
    
    logger.info("Training complete!")
    logger.info(f"Best validation loss: {best_val_loss:.4f}")
    
    # Load best model
    model.load_state_dict(torch.load('models/profitability_predictor_best.pth'))
    return model


async def train_profitability_model_async():
    """Main async training function."""
    # Create models directory
    Path('models').mkdir(exist_ok=True)
    
    # Load trade history with outcomes
    logger.info("Loading trade history...")
    enriched_trades = load_trade_history_with_outcomes()
    
    if len(enriched_trades) < 10:
        logger.error("Not enough trades for training. Need at least 10 trades.")
        logger.info("Run simulations or live trading to generate trade history first.")
        return
    
    # Fetch historical data
    logger.info("Fetching historical market data...")
    sol_ohlc, btc_ohlc = await fetch_historical_data_for_trades(enriched_trades)
    
    if not sol_ohlc or len(sol_ohlc) < 100:
        logger.error("Could not fetch sufficient historical data")
        return
    
    # Create training data
    logger.info("Creating training dataset...")
    X, y = await create_training_data_from_trades(enriched_trades, sol_ohlc, btc_ohlc)
    
    if X is None or len(X) == 0:
        logger.error("Could not create training data")
        return
    
    # Split data
    X_train, X_val, y_train, y_val = split_data(X, y, train_ratio=0.8)
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}")
    
    # Normalize features
    feature_mean = np.mean(X_train, axis=(0, 1), keepdims=True)
    feature_std = np.std(X_train, axis=(0, 1), keepdims=True) + 1e-8
    X_train = (X_train - feature_mean) / feature_std
    X_val = (X_val - feature_mean) / feature_std
    
    # Replace any NaN/Inf
    X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
    X_val = np.nan_to_num(X_val, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Model parameters
    input_size = X_train.shape[2]
    sequence_length = X_train.shape[1]
    
    logger.info(f"Input size: {input_size}, Sequence length: {sequence_length}")
    
    # Create model
    model = ProfitabilityPredictor(
        input_size=input_size,
        hidden_size=64,
        num_layers=2,
        dropout=0.2
    )
    
    # Train
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    
    trained_model = train_profitability_model(
        model, X_train, y_train, X_val, y_val,
        epochs=50,
        batch_size=16,
        learning_rate=0.001,
        device=device
    )
    
    # Save final model
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = f'models/profitability_predictor_{timestamp}.pth'
    torch.save(trained_model.state_dict(), model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Also save as default
    torch.save(trained_model.state_dict(), 'models/profitability_predictor.pth')
    logger.info("Model also saved as models/profitability_predictor.pth")
    
    # Save normalization parameters
    norm_params = {
        'mean': feature_mean.tolist(),
        'std': feature_std.tolist()
    }
    with open('models/profitability_predictor_norm.json', 'w') as f:
        json.dump(norm_params, f)
    logger.info("Normalization parameters saved")


if __name__ == '__main__':
    asyncio.run(train_profitability_model_async())

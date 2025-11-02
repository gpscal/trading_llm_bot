"""
Learn from trading outcomes - Reinforcement Learning from trade history.

This module enables the bot to learn from its own trading performance,
not just market patterns. It tracks which trades were profitable and
adjusts strategy accordingly.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger('trade_learner')


class TradeHistoryAnalyzer:
    """Analyze trade history to learn what works."""
    
    def __init__(self, trade_log_path: str = 'trade_log.json'):
        self.trade_log_path = trade_log_path
        self.trades = []
        
    def load_trade_history(self) -> List[Dict]:
        """Load all trades from log file."""
        if not Path(self.trade_log_path).exists():
            logger.warning(f"Trade log not found at {self.trade_log_path}")
            return []
        
        trades = []
        try:
            with open(self.trade_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            trade = json.loads(line.strip())
                            trades.append(trade)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
        
        self.trades = trades
        logger.info(f"Loaded {len(trades)} trades from history")
        return trades
    
    def analyze_trade_outcomes(self, balance_history: Optional[List] = None) -> Dict:
        """
        Analyze which trades were profitable and extract patterns.
        
        Args:
            balance_history: Optional list of balance snapshots to calculate P&L
        
        Returns:
            Dictionary with:
            - profitable_patterns: Features/conditions that led to profit
            - unprofitable_patterns: Features/conditions that led to loss
            - success_rate_by_condition: Success rate for different conditions
        """
        if not self.trades:
            self.load_trade_history()
        
        if len(self.trades) < 10:
            logger.warning("Not enough trades to analyze (< 10)")
            return {}
        
        # Group trades by action and analyze outcomes
        buy_trades = [t for t in self.trades if t.get('action') == 'buy']
        sell_trades = [t for t in self.trades if t.get('action') == 'sell']
        
        # Calculate profitability by matching buy/sell pairs
        trade_pairs = self._match_trade_pairs(buy_trades, sell_trades)
        
        profitable_conditions = defaultdict(int)
        unprofitable_conditions = defaultdict(int)
        
        # Analyze what made trades profitable
        for pair in trade_pairs:
            buy_trade = pair['buy']
            sell_trade = pair['sell']
            
            # Calculate profit
            profit_pct = ((sell_trade['price'] - buy_trade['price']) / buy_trade['price']) * 100
            is_profitable = profit_pct > 0.5  # More than 0.5% profit (accounting for fees)
            
            # Extract conditions from buy trade
            # Use actual RSI/MACD values from trade log (rsi_btc, rsi_sol, etc.)
            rsi_sol = buy_trade.get('rsi_sol')
            rsi_btc = buy_trade.get('rsi_btc')
            macd_sol = buy_trade.get('macd_sol')
            macd_btc = buy_trade.get('macd_btc')
            
            conditions = {
                'rsi_sol': round(rsi_sol, 1) if rsi_sol is not None else 'unknown',
                'rsi_btc': round(rsi_btc, 1) if rsi_btc is not None else 'unknown',
                'macd_sol': round(macd_sol, 3) if macd_sol is not None else 'unknown',
                'macd_btc': round(macd_btc, 3) if macd_btc is not None else 'unknown',
                'confidence': buy_trade.get('confidence', 'unknown'),
                'time_of_day': self._get_time_of_day(buy_trade.get('timestamp', '')),
            }
            
            # Track patterns
            if is_profitable:
                for condition, value in conditions.items():
                    profitable_conditions[f"{condition}_{value}"] += 1
            else:
                for condition, value in conditions.items():
                    unprofitable_conditions[f"{condition}_{value}"] += 1
        
        # Calculate success rates
        success_rate = {}
        all_conditions = set(list(profitable_conditions.keys()) + list(unprofitable_conditions.keys()))
        
        for condition in all_conditions:
            profitable = profitable_conditions.get(condition, 0)
            unprofitable = unprofitable_conditions.get(condition, 0)
            total = profitable + unprofitable
            if total > 0:
                success_rate[condition] = profitable / total
        
        return {
            'profitable_patterns': dict(profitable_conditions),
            'unprofitable_patterns': dict(unprofitable_conditions),
            'success_rate_by_condition': success_rate,
            'total_trades': len(trade_pairs),
            'profitable_trades': sum(1 for p in trade_pairs if self._calculate_profit(p) > 0),
        }
    
    def _match_trade_pairs(self, buy_trades: List, sell_trades: List) -> List[Dict]:
        """Match buy trades with subsequent sell trades."""
        pairs = []
        buy_trades = sorted(buy_trades, key=lambda x: x.get('timestamp', ''))
        sell_trades = sorted(sell_trades, key=lambda x: x.get('timestamp', ''))
        
        for buy in buy_trades:
            # Find next sell after this buy
            buy_time = buy.get('timestamp', '')
            matching_sell = None
            
            for sell in sell_trades:
                if sell.get('timestamp', '') > buy_time:
                    matching_sell = sell
                    break
            
            if matching_sell:
                pairs.append({'buy': buy, 'sell': matching_sell})
        
        return pairs
    
    def _calculate_profit(self, pair: Dict) -> float:
        """Calculate profit percentage for a trade pair."""
        buy_price = pair['buy'].get('price', 0)
        sell_price = pair['sell'].get('price', 0)
        if buy_price > 0:
            return ((sell_price - buy_price) / buy_price) * 100
        return 0
    
    def _get_time_of_day(self, timestamp: str) -> str:
        """Extract time of day from timestamp."""
        try:
            # Parse timestamp and get hour
            dt = datetime.fromisoformat(timestamp.replace(' ', 'T'))
            hour = dt.hour
            if 0 <= hour < 6:
                return 'night'
            elif 6 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 18:
                return 'afternoon'
            else:
                return 'evening'
        except:
            return 'unknown'
    
    def get_optimal_confidence_threshold(self) -> Optional[float]:
        """Find optimal confidence threshold based on trade outcomes."""
        analysis = self.analyze_trade_outcomes()
        if not analysis:
            return None
        
        # Analyze success rate by confidence level
        # This is simplified - in production, would use more sophisticated analysis
        success_rates = analysis.get('success_rate_by_condition', {})
        
        confidence_success = {}
        for condition, rate in success_rates.items():
            if condition.startswith('confidence_'):
                try:
                    conf_level = float(condition.split('_')[1])
                    confidence_success[conf_level] = rate
                except:
                    pass
        
        if confidence_success:
            # Find confidence level with highest success rate
            optimal = max(confidence_success.items(), key=lambda x: x[1])
            logger.info(f"Optimal confidence threshold: {optimal[0]:.2f} (success rate: {optimal[1]:.2%})")
            return optimal[0]
        
        return None


class ReinforcementLearner:
    """
    Reinforcement Learning system that learns from trading outcomes.
    
    Uses Q-learning or policy gradient to optimize trading strategy
    based on reward (profit) from past trades.
    """
    
    def __init__(self, state_size: int = 20, action_size: int = 3):
        """
        Initialize RL agent.
        
        Args:
            state_size: Number of features in state (indicators + market data)
            action_size: Number of actions (buy, sell, hold)
        """
        self.state_size = state_size
        self.action_size = action_size
        self.q_table = defaultdict(lambda: np.zeros(action_size))
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1  # Exploration rate
        
    def get_action(self, state: np.ndarray, use_policy: bool = True) -> int:
        """
        Choose action based on state.
        
        Args:
            state: Feature vector (flattened)
            use_policy: If True, use learned policy; else random (exploration)
        
        Returns:
            Action: 0=buy, 1=sell, 2=hold
        """
        state_key = tuple(np.round(state, 2))
        
        if use_policy and state_key in self.q_table:
            # Exploit: choose best action
            return np.argmax(self.q_table[state_key])
        else:
            # Explore: random action
            return np.random.randint(self.action_size)
    
    def update_q_value(self, state: np.ndarray, action: int, reward: float, 
                       next_state: Optional[np.ndarray] = None):
        """
        Update Q-value based on reward.
        
        Q(s,a) = Q(s,a) + lr * [reward + discount * max(Q(s',a')) - Q(s,a)]
        """
        state_key = tuple(np.round(state, 2))
        current_q = self.q_table[state_key][action]
        
        if next_state is not None:
            next_state_key = tuple(np.round(next_state, 2))
            next_max_q = np.max(self.q_table[next_state_key])
            target_q = reward + self.discount_factor * next_max_q
        else:
            target_q = reward
        
        # Q-learning update
        self.q_table[state_key][action] = current_q + self.learning_rate * (target_q - current_q)
    
    def train_from_history(self, trade_history: List[Dict], state_history: List[np.ndarray]):
        """
        Train RL agent from historical trades.
        
        Args:
            trade_history: List of trade records with outcomes
            state_history: Corresponding state vectors for each trade
        """
        if len(trade_history) != len(state_history):
            logger.error("Trade history and state history length mismatch")
            return
        
        logger.info(f"Training RL agent on {len(trade_history)} historical trades...")
        
        # Calculate rewards (profit/loss) for each trade
        for i, (trade, state) in enumerate(zip(trade_history, state_history)):
            # Extract action from trade
            action_map = {'buy': 0, 'sell': 1, 'hold': 2}
            action = action_map.get(trade.get('action', 'hold'), 2)
            
            # Calculate reward (profit percentage)
            reward = trade.get('profit_pct', 0.0)
            
            # Update Q-value
            next_state = state_history[i + 1] if i + 1 < len(state_history) else None
            self.update_q_value(state, action, reward, next_state)
        
        logger.info(f"Training complete. Q-table size: {len(self.q_table)}")
    
    def save_model(self, path: str = 'models/rl_agent.pkl'):
        """Save trained RL agent."""
        import pickle
        Path(path).parent.mkdir(exist_ok=True, parents=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'q_table': dict(self.q_table),
                'state_size': self.state_size,
                'action_size': self.action_size,
            }, f)
        logger.info(f"RL agent saved to {path}")
    
    def load_model(self, path: str = 'models/rl_agent.pkl'):
        """Load trained RL agent."""
        import pickle
        if not Path(path).exists():
            logger.warning(f"RL model not found at {path}")
            return False
        
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.q_table = defaultdict(lambda: np.zeros(self.action_size), data['q_table'])
            self.state_size = data['state_size']
            self.action_size = data['action_size']
        
        logger.info(f"RL agent loaded from {path}. Q-table size: {len(self.q_table)}")
        return True


def learn_from_trading_outcomes() -> Dict:
    """
    Main function to learn from trading history.
    
    Returns:
        Dictionary with learned patterns and recommendations
    """
    analyzer = TradeHistoryAnalyzer()
    analysis = analyzer.analyze_trade_outcomes()
    
    recommendations = {
        'optimal_confidence_threshold': analyzer.get_optimal_confidence_threshold(),
        'profitable_conditions': analysis.get('profitable_patterns', {}),
        'unprofitable_conditions': analysis.get('unprofitable_patterns', {}),
        'success_rates': analysis.get('success_rate_by_condition', {}),
        'total_trades': analysis.get('total_trades', 0),
        'profitability_rate': analysis.get('profitable_trades', 0) / max(analysis.get('total_trades', 1), 1),
    }
    
    logger.info(f"Analysis complete:")
    logger.info(f"  Total trades: {recommendations['total_trades']}")
    logger.info(f"  Profitability rate: {recommendations['profitability_rate']:.2%}")
    logger.info(f"  Optimal confidence: {recommendations['optimal_confidence_threshold']}")
    
    return recommendations


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    recommendations = learn_from_trading_outcomes()
    print(json.dumps(recommendations, indent=2))

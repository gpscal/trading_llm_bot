"""
Signal Change Tracker
Tracks trading signal changes and triggers notifications
Also maintains signal history for stability checking
"""
import os
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from collections import deque
from utils.logger import setup_logger

logger = setup_logger('signal_tracker', 'signal_tracker.log')


class SignalTracker:
    """Tracks trading signals and detects changes"""
    
    def __init__(self, state_file: str = 'signal_state.json', history_size: int = 5):
        self.state_file = state_file
        self.signals = {}  # {coin: signal}
        self.signal_history = {}  # {coin: deque([(signal, timestamp), ...])}
        self.history_size = history_size  # Max history entries per coin
        self._load_state()
    
    def _load_state(self):
        """Load previous signal state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.signals = data.get('signals', {})
                    
                    # Load signal history (convert lists back to deques)
                    history_data = data.get('signal_history', {})
                    self.signal_history = {
                        coin: deque(history, maxlen=self.history_size)
                        for coin, history in history_data.items()
                    }
                    
                    logger.info(f"Loaded signal state: {self.signals}")
                    if self.signal_history:
                        logger.debug(f"Loaded signal history: {dict(self.signal_history)}")
            except Exception as e:
                logger.error(f"Failed to load signal state: {e}")
                self.signals = {}
                self.signal_history = {}
        else:
            logger.info("No previous signal state found, starting fresh")
    
    def _save_state(self):
        """Save current signal state to file"""
        try:
            # Convert deques to lists for JSON serialization
            history_data = {
                coin: list(history)
                for coin, history in self.signal_history.items()
            }
            
            data = {
                'signals': self.signals,
                'signal_history': history_data,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved signal state: {self.signals}")
        except Exception as e:
            logger.error(f"Failed to save signal state: {e}")
    
    def check_signal_change(self, coin: str, new_signal: str) -> tuple[bool, Optional[str]]:
        """
        Check if signal has changed for a coin and update history
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            new_signal: New signal value ('BUY', 'SELL', 'HOLD')
        
        Returns:
            Tuple of (has_changed: bool, old_signal: str|None)
        """
        coin = coin.upper()
        old_signal = self.signals.get(coin)
        timestamp = datetime.now().isoformat()
        
        # Initialize history for this coin if not exists
        if coin not in self.signal_history:
            self.signal_history[coin] = deque(maxlen=self.history_size)
        
        # Add to history
        self.signal_history[coin].append((new_signal, timestamp))
        
        # First time seeing this coin
        if old_signal is None:
            logger.info(f"First signal for {coin}: {new_signal}")
            self.signals[coin] = new_signal
            self._save_state()
            return False, None
        
        # Check for change
        if old_signal != new_signal:
            logger.info(f"Signal change detected for {coin}: {old_signal} → {new_signal}")
            self.signals[coin] = new_signal
            self._save_state()
            return True, old_signal
        
        # No change
        return False, old_signal
    
    def get_current_signal(self, coin: str) -> Optional[str]:
        """Get current signal for a coin"""
        return self.signals.get(coin.upper())
    
    def get_signal_history(self, coin: str, count: Optional[int] = None) -> List[Tuple[str, str]]:
        """
        Get signal history for a coin
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            count: Number of recent signals to return (None = all)
        
        Returns:
            List of (signal, timestamp) tuples, most recent last
        """
        coin = coin.upper()
        if coin not in self.signal_history:
            return []
        
        history = list(self.signal_history[coin])
        if count is not None:
            history = history[-count:]
        
        return history
    
    def check_signal_stability(self, coin: str, required_count: int = 2) -> Tuple[bool, Optional[str]]:
        """
        Check if the last N signals are stable (all the same)
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            required_count: Number of consecutive agreeing signals required
        
        Returns:
            Tuple of (is_stable: bool, stable_signal: str|None)
        """
        coin = coin.upper()
        history = self.get_signal_history(coin, count=required_count)
        
        # Not enough history
        if len(history) < required_count:
            logger.debug(f"Signal stability check for {coin}: Not enough history "
                        f"({len(history)}/{required_count} signals)")
            return False, None
        
        # Check if all signals match
        signals = [sig for sig, _ in history]
        if len(set(signals)) == 1:
            stable_signal = signals[0]
            logger.info(f"Signal stability check for {coin}: ✓ STABLE - "
                       f"Last {required_count} signals all {stable_signal}")
            return True, stable_signal
        else:
            logger.info(f"Signal stability check for {coin}: ✗ UNSTABLE - "
                       f"Last {required_count} signals: {signals}")
            return False, None
    
    def reset_signal(self, coin: str):
        """Reset signal tracking for a coin"""
        coin = coin.upper()
        if coin in self.signals:
            del self.signals[coin]
        if coin in self.signal_history:
            del self.signal_history[coin]
        self._save_state()
        logger.info(f"Reset signal and history for {coin}")
    
    def reset_all(self):
        """Reset all signal tracking"""
        self.signals = {}
        self.signal_history = {}
        self._save_state()
        logger.info("Reset all signals and history")


# Global instance
_signal_tracker_instance = None


def get_signal_tracker() -> SignalTracker:
    """Get or create signal tracker instance"""
    global _signal_tracker_instance
    
    if _signal_tracker_instance is None:
        _signal_tracker_instance = SignalTracker()
    
    return _signal_tracker_instance

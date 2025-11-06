"""
Signal Change Tracker
Tracks trading signal changes and triggers notifications
"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger('signal_tracker', 'signal_tracker.log')


class SignalTracker:
    """Tracks trading signals and detects changes"""
    
    def __init__(self, state_file: str = 'signal_state.json'):
        self.state_file = state_file
        self.signals = {}  # {coin: signal}
        self._load_state()
    
    def _load_state(self):
        """Load previous signal state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.signals = data.get('signals', {})
                    logger.info(f"Loaded signal state: {self.signals}")
            except Exception as e:
                logger.error(f"Failed to load signal state: {e}")
                self.signals = {}
        else:
            logger.info("No previous signal state found, starting fresh")
    
    def _save_state(self):
        """Save current signal state to file"""
        try:
            data = {
                'signals': self.signals,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved signal state: {self.signals}")
        except Exception as e:
            logger.error(f"Failed to save signal state: {e}")
    
    def check_signal_change(self, coin: str, new_signal: str) -> tuple[bool, Optional[str]]:
        """
        Check if signal has changed for a coin
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            new_signal: New signal value ('BUY', 'SELL', 'HOLD')
        
        Returns:
            Tuple of (has_changed: bool, old_signal: str|None)
        """
        coin = coin.upper()
        old_signal = self.signals.get(coin)
        
        # First time seeing this coin
        if old_signal is None:
            logger.info(f"First signal for {coin}: {new_signal}")
            self.signals[coin] = new_signal
            self._save_state()
            return False, None
        
        # Check for change
        if old_signal != new_signal:
            logger.info(f"Signal change detected for {coin}: {old_signal} ? {new_signal}")
            self.signals[coin] = new_signal
            self._save_state()
            return True, old_signal
        
        # No change
        return False, old_signal
    
    def get_current_signal(self, coin: str) -> Optional[str]:
        """Get current signal for a coin"""
        return self.signals.get(coin.upper())
    
    def reset_signal(self, coin: str):
        """Reset signal tracking for a coin"""
        coin = coin.upper()
        if coin in self.signals:
            del self.signals[coin]
            self._save_state()
            logger.info(f"Reset signal for {coin}")
    
    def reset_all(self):
        """Reset all signal tracking"""
        self.signals = {}
        self._save_state()
        logger.info("Reset all signals")


# Global instance
_signal_tracker_instance = None


def get_signal_tracker() -> SignalTracker:
    """Get or create signal tracker instance"""
    global _signal_tracker_instance
    
    if _signal_tracker_instance is None:
        _signal_tracker_instance = SignalTracker()
    
    return _signal_tracker_instance

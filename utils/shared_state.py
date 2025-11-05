import threading
from typing import Any, Dict, Optional

from config.config import CONFIG

# Thread-safe shared state lock
# When using eventlet workers, the threading module is monkey-patched automatically
# We use RLock which eventlet handles better than Lock
_lock = None

def _get_lock():
    """Get or create the thread lock (lazy initialization for eventlet compatibility)."""
    global _lock
    if _lock is None:
        # Check if we're in an eventlet environment and use appropriate lock
        try:
            import eventlet
            # If eventlet has monkey-patched, use the patched version
            # RLock works better with eventlet's green threading
            _lock = threading.RLock()
        except ImportError:
            # Standard threading if eventlet not available
            _lock = threading.RLock()
    return _lock

def reset_lock():
    """Reset the lock (useful after eventlet monkey-patching in worker processes)."""
    global _lock
    _lock = None

# Flask app instance (needed for app context in background threads)
_app_instance: Optional[Any] = None

# SocketIO instance for WebSocket emits (set by Flask app)
_socketio_instance: Optional[Any] = None

bot_state = {
    "running": False,
    "mode": None,
    "selected_coin": CONFIG.get('default_coin', 'SOL').upper(),
    "balance": {
        "usdt": CONFIG.get('initial_balance_usdt', 0.0),
        "coins": {
            coin: {
                "amount": CONFIG.get('initial_coin_balances', {}).get(coin, 0.0),
                "price": 0.0,
                "indicators": {},
                "historical": [],
                "position_entry_price": None,
                "trailing_high_price": None,
            }
            for coin in CONFIG.get('tradable_coins', [])
        }
    },
    "logs": [],
    "indicators": {},
    "price_history": [],  # Primary coin price history for charting
    "btc_price_history": [],
    # Enhanced metrics for dashboard and risk
    "equity_history": [],
    "drawdown_history": [],
    # Time-series indicator history for charts
    "indicator_history": {
        coin.lower(): [] for coin in CONFIG.get('tradable_coins', [])
    },
    "coin_trade_history": {
        coin: [] for coin in CONFIG.get('tradable_coins', [])
    }
}

def set_socketio_instance(socketio):
    """Set the SocketIO instance for emitting WebSocket events."""
    global _socketio_instance
    _socketio_instance = socketio

def set_app_instance(app):
    """Set the Flask app instance for application context in background threads."""
    global _app_instance
    _app_instance = app

def set_socketio_and_app(socketio, app):
    """Convenience method to set both SocketIO and Flask app instances."""
    set_socketio_instance(socketio)
    set_app_instance(app)

def update_bot_state(new_data: Dict[str, Any]) -> None:
    """Update bot state without thread safety (deprecated, use update_bot_state_safe)."""
    bot_state.update(new_data)
    # If SocketIO is running, it can be emitted separately or integrate here

def _emit_status_update():
    """Internal function to emit status update with proper context."""
    if _socketio_instance is not None and _app_instance is not None:
        try:
            # Get state copy before emitting
            state_copy = get_bot_state_safe()
            
            # Try emitting with app context first
            with _app_instance.app_context():
                _socketio_instance.emit('status_update', state_copy, namespace='/', broadcast=True)
        except RuntimeError as e:
            # RuntimeError: Working outside of request context
            # This happens when Flask-SocketIO tries to access request-local proxies
            # It's safe to suppress this error - the emit may still work or we can retry without context
            error_msg = str(e).lower()
            if "request context" in error_msg or "working outside" in error_msg:
                # Try emitting without explicit context (may work if SocketIO handles it internally)
                try:
                    _socketio_instance.emit('status_update', state_copy, namespace='/', broadcast=True)
                except:
                    # If that also fails, just skip the emit
                    pass
            else:
                # Re-raise if it's a different RuntimeError
                raise
        except Exception:
            # Silently fail for other exceptions (e.g., no clients connected)
            pass

def update_bot_state_safe(new_data: Dict[str, Any]) -> None:
    """Thread-safe update of bot state.
    
    For nested updates (like appending to lists), this merges safely:
    - Dicts are updated (merged)
    - Lists are replaced (caller should handle appends in new_data if needed)
    
    Emits 'status_update' WebSocket event if SocketIO instance is available.
    """
    with _get_lock():
        # Handle nested dict updates
        for key, value in new_data.items():
            if isinstance(value, dict) and isinstance(bot_state.get(key), dict):
                bot_state[key].update(value)
            else:
                bot_state[key] = value
    
    # Emit WebSocket update if SocketIO instance is available (outside lock)
    _emit_status_update()

def get_bot_state_safe() -> Dict[str, Any]:
    """Thread-safe read of bot state (returns a shallow copy)."""
    with _get_lock():
        return dict(bot_state)

def _emit_log_update(message: str):
    """Internal function to emit log update with proper context."""
    if _socketio_instance is not None and _app_instance is not None:
        try:
            # Try emitting with app context first
            with _app_instance.app_context():
                _socketio_instance.emit('log_update', {'message': message}, namespace='/', broadcast=True)
        except RuntimeError as e:
            # RuntimeError: Working outside of request context
            # This happens when Flask-SocketIO tries to access request-local proxies
            # It's safe to suppress this error - the emit may still work or we can retry without context
            error_msg = str(e).lower()
            if "request context" in error_msg or "working outside" in error_msg:
                # Try emitting without explicit context (may work if SocketIO handles it internally)
                try:
                    _socketio_instance.emit('log_update', {'message': message}, namespace='/', broadcast=True)
                except:
                    # If that also fails, just skip the emit
                    pass
            else:
                # Re-raise if it's a different RuntimeError
                raise
        except Exception:
            # Silently fail for other exceptions (e.g., no clients connected)
            pass

def append_log_safe(message: str) -> None:
    """Thread-safe append to logs list.
    
    Emits 'log_update' WebSocket event if SocketIO instance is available.
    """
    with _get_lock():
        if "logs" not in bot_state:
            bot_state["logs"] = []
        bot_state["logs"].append(message)
        # Keep logs manageable (keep last 1000 entries)
        if len(bot_state["logs"]) > 1000:
            bot_state["logs"] = bot_state["logs"][-1000:]
    
    # Emit WebSocket log update if SocketIO instance is available
    _emit_log_update(message)

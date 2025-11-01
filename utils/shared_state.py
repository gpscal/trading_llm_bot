import threading
from typing import Any, Dict, Optional

# Thread-safe shared state
_lock = threading.Lock()

# SocketIO instance for WebSocket emits (set by Flask app)
_socketio_instance: Optional[Any] = None

bot_state = {
    "running": False,
    "mode": None,
    "balance": {},
    "logs": [],
    "indicators": {},
    "price_history": [],  # SOL price history for charting
    "btc_price_history": [],
    # Enhanced metrics for dashboard and risk
    "equity_history": [],
    "drawdown_history": [],
    # Time-series indicator history for charts
    "indicator_history": {
        "btc": [],
        "sol": []
    }
}

def set_socketio_instance(socketio):
    """Set the SocketIO instance for emitting WebSocket events."""
    global _socketio_instance
    _socketio_instance = socketio

def update_bot_state(new_data: Dict[str, Any]) -> None:
    """Update bot state without thread safety (deprecated, use update_bot_state_safe)."""
    bot_state.update(new_data)
    # If SocketIO is running, it can be emitted separately or integrate here

def update_bot_state_safe(new_data: Dict[str, Any]) -> None:
    """Thread-safe update of bot state.
    
    For nested updates (like appending to lists), this merges safely:
    - Dicts are updated (merged)
    - Lists are replaced (caller should handle appends in new_data if needed)
    
    Emits 'status_update' WebSocket event if SocketIO instance is available.
    """
    with _lock:
        # Handle nested dict updates
        for key, value in new_data.items():
            if isinstance(value, dict) and isinstance(bot_state.get(key), dict):
                bot_state[key].update(value)
            else:
                bot_state[key] = value
    
    # Emit WebSocket update if SocketIO instance is available (outside lock)
    if _socketio_instance is not None:
        try:
            _socketio_instance.emit('status_update', get_bot_state_safe())
        except Exception:
            # Silently fail if emit fails (e.g., no clients connected)
            pass

def get_bot_state_safe() -> Dict[str, Any]:
    """Thread-safe read of bot state (returns a shallow copy)."""
    with _lock:
        return dict(bot_state)

def append_log_safe(message: str) -> None:
    """Thread-safe append to logs list.
    
    Emits 'log_update' WebSocket event if SocketIO instance is available.
    """
    with _lock:
        if "logs" not in bot_state:
            bot_state["logs"] = []
        bot_state["logs"].append(message)
        # Keep logs manageable (keep last 1000 entries)
        if len(bot_state["logs"]) > 1000:
            bot_state["logs"] = bot_state["logs"][-1000:]
    
    # Emit WebSocket log update if SocketIO instance is available
    if _socketio_instance is not None:
        try:
            _socketio_instance.emit('log_update', {'message': message})
        except Exception:
            # Silently fail if emit fails (e.g., no clients connected)
            pass

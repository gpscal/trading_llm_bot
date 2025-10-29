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
    "drawdown_history": []
    ,
    # Time-series indicator history for charts
    "indicator_history": {
        "btc": [],
        "sol": []
    }
}

# To integrate with Flask SocketIO, you can pass socketio or make it optional
# For now, keep simple; Streamlit polls anyway

def update_bot_state(new_data):
    bot_state.update(new_data)
    # If SocketIO is running, it can be emitted separately or integrate here

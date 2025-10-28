bot_state = {
    "running": False,
    "mode": None,
    "balance": {},
    "logs": [],
    "indicators": {},
    "price_history": []  # Example for charting
}

def update_bot_state(new_data):
    bot_state.update(new_data)
    # If using SocketIO, emit here (but since it's in web/app.py, call from there)

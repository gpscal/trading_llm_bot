from flask import Flask, jsonify, request
from flask_socketio import SocketIO
import threading
from simulate import main as simulate_main
from live_trade import live_trade as live_trade_main
import asyncio

app = Flask(__name__)
socketio = SocketIO(app)

# Shared state for bot data
bot_state = {
    "running": False,
    "mode": None,  # 'simulation' or 'live'
    "balance": {},
    "logs": [],
    "indicators": {}
}

def update_bot_state(new_data):
    bot_state.update(new_data)
    socketio.emit('update', bot_state)

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    if not bot_state['running']:
        data = request.json
        initial_usdt = data.get('initial_usdt', 1000)
        initial_sol = data.get('initial_sol', 10)
        threading.Thread(target=lambda: asyncio.run(simulate_main(initial_usdt, initial_sol))).start()
        bot_state['running'] = True
        bot_state['mode'] = 'simulation'
        return jsonify({"status": "Simulation started"})
    return jsonify({"error": "Already running"}), 400

@app.route('/start_live', methods=['POST'])
def start_live():
    if not bot_state['running']:
        threading.Thread(target=lambda: asyncio.run(live_trade_main())).start()
        bot_state['running'] = True
        bot_state['mode'] = 'live'
        return jsonify({"status": "Live trading started"})
    return jsonify({"error": "Already running"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    if bot_state['running']:
        # Note: Implement proper shutdown logic in bot code
        bot_state['running'] = False
        bot_state['mode'] = None
        return jsonify({"status": "Stopped"})
    return jsonify({"error": "Not running"}), 400

@app.route('/get_status')
def get_status():
    return jsonify(bot_state)

@socketio.on('connect')
def handle_connect():
    socketio.emit('update', bot_state)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)

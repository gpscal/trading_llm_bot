import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
import threading
from simulate import main as simulate_main
from live_trade import live_trade as live_trade_main
import asyncio
import numpy as np
import json

# Import shared state
from utils.shared_state import bot_state, update_bot_state_safe, get_bot_state_safe, set_socketio_instance
from utils.config_manager import load_profiles, save_profile, apply_profile, mask_value

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts numpy types to Python types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        return super().default(obj)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.json_encoder = NumpyEncoder
socketio = SocketIO(app, cors_allowed_origins="*")

# Set socketio instance in shared_state module for WebSocket emits
set_socketio_instance(socketio)

# Route to serve dashboard HTML
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Static file serving is handled automatically by Flask via static_folder

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    state = get_bot_state_safe()
    if not state['running']:
        data = request.json
        initial_usdt = data.get('initial_usdt', 1000)
        initial_sol = data.get('initial_sol', 10)
        threading.Thread(target=lambda: asyncio.run(simulate_main(initial_usdt, initial_sol))).start()
        update_bot_state_safe({'running': True, 'mode': 'simulation'})
        # Emit WebSocket update
        socketio.emit('status_update', get_bot_state_safe())
        return jsonify({"status": "Simulation started"})
    return jsonify({"error": "Already running"}), 400

@app.route('/start_live', methods=['POST'])
def start_live():
    state = get_bot_state_safe()
    if not state['running']:
        threading.Thread(target=lambda: asyncio.run(live_trade_main())).start()
        update_bot_state_safe({'running': True, 'mode': 'live'})
        # Emit WebSocket update
        socketio.emit('status_update', get_bot_state_safe())
        return jsonify({"status": "Live trading started"})
    return jsonify({"error": "Already running"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    state = get_bot_state_safe()
    if state['running']:
        # Note: Implement proper shutdown logic in bot code
        update_bot_state_safe({'running': False, 'mode': None})
        # Emit WebSocket update
        socketio.emit('status_update', get_bot_state_safe())
        return jsonify({"status": "Stopped"})
    return jsonify({"error": "Not running"}), 400

@app.route('/get_status')
def get_status():
    # Convert numpy types to Python types before JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        else:
            return obj

    serializable_state = convert_numpy_types(get_bot_state_safe())
    return jsonify(serializable_state)

@app.route('/profiles', methods=['GET'])
def list_profiles():
    profiles = load_profiles()
    # Return masked values for display
    masked = {}
    for name, vals in profiles.items():
        masked[name] = {k: mask_value(v) for k, v in vals.items()}
    return jsonify(masked)

@app.route('/save_profile', methods=['POST'])
def save_profile_route():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing profile name'}), 400
    values = {
        'api_key': data.get('api_key'),
        'api_secret': data.get('api_secret'),
        'slack_webhook_url': data.get('slack_webhook_url'),
        'telegram_bot_token': data.get('telegram_bot_token'),
        'telegram_chat_id': data.get('telegram_chat_id'),
    }
    save_profile(name, values)
    return jsonify({'status': 'saved'})

@app.route('/apply_profile', methods=['POST'])
def apply_profile_route():
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing profile name'}), 400
    try:
        applied = apply_profile(name)
        return jsonify({'status': 'applied', 'applied_keys': list(applied.keys())})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@socketio.on('connect')
def handle_connect():
    """Handle client WebSocket connection - send initial state"""
    socketio.emit('status_update', get_bot_state_safe())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    pass

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)

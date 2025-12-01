import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Monkey-patch eventlet if running with eventlet workers (for Gunicorn)
# This must happen before importing threading or any modules that use locks
# Note: wsgi.py already does this, but we do it here too for direct Flask runs
try:
    import eventlet
    # Try to monkey-patch (idempotent - safe to call multiple times)
    eventlet.monkey_patch()
except ImportError:
    # eventlet not available, continue with standard threading
    pass

from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO
import threading
from simulate import main as simulate_main
from live_trade import live_trade as live_trade_main
import asyncio
import numpy as np
import json

# Import shared state
from utils.shared_state import bot_state, update_bot_state_safe, get_bot_state_safe, set_socketio_and_app, append_log_safe
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

# Set socketio and app instances in shared_state module for WebSocket emits
# This enables proper Flask app context for background thread emits
set_socketio_and_app(socketio, app)

# Store thread references for proper management
_simulation_thread = None
_live_trading_thread = None

# Route to serve dashboard HTML
@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Static file serving is handled automatically by Flask via static_folder

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    global _simulation_thread
    import subprocess
    
    # Check if systemd simulation service is running (user or system service)
    try:
        # Try system service first
        result = subprocess.run(['systemctl', 'is-active', 'trading_llm_bot_simulation'], 
                               capture_output=True, text=True, timeout=2)
        systemd_running = result.returncode == 0 and result.stdout.strip() == 'active'
        
        # If not system service, try user service
        if not systemd_running:
            result = subprocess.run(['systemctl', '--user', 'is-active', 'trading_llm_bot_simulation'], 
                                   capture_output=True, text=True, timeout=2)
            systemd_running = result.returncode == 0 and result.stdout.strip() == 'active'
    except:
        systemd_running = False
    
    # Check if web thread is running
    thread_running = _simulation_thread is not None and _simulation_thread.is_alive()
    
    state = get_bot_state_safe()
    state_running = state.get('running', False)
    
    # If something is already running, return error
    if systemd_running or thread_running or state_running:
        return jsonify({
            "error": "Simulation already running",
            "details": {
                "systemd_service": systemd_running,
                "web_thread": thread_running,
                "shared_state": state_running
            }
        }), 400
    
    data = request.json
    initial_usdt = data.get('initial_usdt', 1000)
    initial_sol = data.get('initial_sol', 10)
    
    def run_simulation():
        try:
            # Run the simulation - it will continue until explicitly stopped
            asyncio.run(simulate_main(initial_usdt, initial_sol))
        except Exception as e:
            import traceback
            error_msg = f"Simulation error: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            update_bot_state_safe({'running': False, 'mode': None})
            append_log_safe(error_msg)
        finally:
            # Ensure state is cleared when simulation ends
            update_bot_state_safe({'running': False, 'mode': None})
    
    # Use non-daemon thread so it persists independently of the web server
    _simulation_thread = threading.Thread(target=run_simulation, daemon=False, name="TradingLLMBot-Simulation")
    _simulation_thread.start()
    update_bot_state_safe({'running': True, 'mode': 'simulation'})
    # Emit WebSocket update
    socketio.emit('status_update', get_bot_state_safe())
    return jsonify({"status": "Simulation started"})

@app.route('/start_live', methods=['POST'])
def start_live():
    global _live_trading_thread
    state = get_bot_state_safe()
    if not state['running']:
        def run_live_trading():
            try:
                asyncio.run(live_trade_main())
            except Exception as e:
                import traceback
                error_msg = f"Live trading error: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                update_bot_state_safe({'running': False, 'mode': None})
                append_log_safe(error_msg)
            finally:
                update_bot_state_safe({'running': False, 'mode': None})
        
        # Use non-daemon thread so it persists independently of the web server
        _live_trading_thread = threading.Thread(target=run_live_trading, daemon=False, name="TradingLLMBot-LiveTrading")
        _live_trading_thread.start()
        update_bot_state_safe({'running': True, 'mode': 'live'})
        # Emit WebSocket update
        socketio.emit('status_update', get_bot_state_safe())
        return jsonify({"status": "Live trading started"})
    return jsonify({"error": "Already running"}), 400

@app.route('/stop', methods=['POST'])
def stop():
    import subprocess
    
    # Check if systemd simulation service is running
    systemd_running = False
    try:
        result = subprocess.run(['systemctl', 'is-active', 'trading_llm_bot_simulation'], 
                               capture_output=True, text=True, timeout=2)
        systemd_running = result.returncode == 0 and result.stdout.strip() == 'active'
    except:
        pass
    
    state = get_bot_state_safe()
    thread_running = _simulation_thread is not None and _simulation_thread.is_alive()
    
    # Stop systemd service if running
    if systemd_running:
        try:
            # Try to stop system service first
            result = subprocess.run(['sudo', 'systemctl', 'stop', 'trading_llm_bot_simulation'], 
                                  capture_output=True, timeout=5)
            # If system service not found, try user service
            if result.returncode != 0:
                subprocess.run(['systemctl', '--user', 'stop', 'trading_llm_bot_simulation'], 
                             capture_output=True, timeout=5)
            update_bot_state_safe({'running': False, 'mode': None})
            socketio.emit('status_update', get_bot_state_safe())
            return jsonify({"status": "Stopped systemd simulation service"})
        except Exception as e:
            return jsonify({"error": f"Failed to stop systemd service: {e}"}), 500
    
    # Stop web thread if running
    if thread_running or state.get('running'):
        update_bot_state_safe({'running': False, 'mode': None})
        socketio.emit('status_update', get_bot_state_safe())
        return jsonify({"status": "Stopped"})
    
    return jsonify({"error": "Not running"}), 400

@app.route('/get_status')
def get_status():
    import subprocess
    
    # Check if systemd simulation service is running (user or system)
    systemd_running = False
    try:
        # Try system service first
        result = subprocess.run(['systemctl', 'is-active', 'trading_llm_bot_simulation'], 
                               capture_output=True, text=True, timeout=2)
        systemd_running = result.returncode == 0 and result.stdout.strip() == 'active'
        
        # If not system service, try user service
        if not systemd_running:
            result = subprocess.run(['systemctl', '--user', 'is-active', 'trading_llm_bot_simulation'], 
                                   capture_output=True, text=True, timeout=2)
            systemd_running = result.returncode == 0 and result.stdout.strip() == 'active'
    except:
        pass
    
    # Get state from shared memory
    state = get_bot_state_safe()
    
    # If systemd service is running but shared state says not running, update shared state
    # This is safe because we're detecting it from the web process
    if systemd_running and not state.get('running'):
        update_bot_state_safe({'running': True, 'mode': 'simulation'})
        state = get_bot_state_safe()  # Refresh state after update
    
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

    # Use the updated state (not get_bot_state_safe() again to avoid race condition)
    serializable_state = convert_numpy_types(state)
    # Add systemd detection info
    serializable_state['systemd_running'] = systemd_running
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
        'discord_bot_token': data.get('discord_bot_token'),
        'discord_channel_id': data.get('discord_channel_id'),
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

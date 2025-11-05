"""
WSGI entry point for running the simulation as a Gunicorn service.

This module provides a simple Flask application that runs the simulation
in a background eventlet greenlet, allowing it to run continuously as a service.
"""

# CRITICAL: Monkey-patch eventlet BEFORE any other imports
import eventlet
eventlet.monkey_patch()

import sys
import os
import logging
from flask import Flask, jsonify

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.FileHandler('simulate_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simulate_wsgi')

# Import simulation components
from config.config import CONFIG
from utils.shared_state import get_bot_state_safe

# Create Flask app
app = Flask(__name__)

# Global variable to track simulation greenlet
simulation_greenlet = None
simulation_running = False


def run_simulation_async():
    """Run the simulation in an async context."""
    import asyncio
    from simulate import main
    
    # Get configuration from environment or config
    initial_balance_usdt = CONFIG['initial_balance_usdt']
    initial_balance_sol = CONFIG['initial_balance_sol']
    initial_balance_btc = CONFIG['initial_balance_btc']
    selected_coin = CONFIG['default_coin']
    
    logger.info(f"Starting simulation with coin={selected_coin}, "
                f"USDT={initial_balance_usdt}, SOL={initial_balance_sol}, BTC={initial_balance_btc}")
    
    # Run the simulation
    try:
        asyncio.run(main(initial_balance_usdt, initial_balance_sol, initial_balance_btc, selected_coin))
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
    finally:
        global simulation_running
        simulation_running = False
        logger.info("Simulation ended")


def start_simulation():
    """Start the simulation in a background greenlet."""
    global simulation_greenlet, simulation_running
    
    if simulation_running:
        logger.warning("Simulation already running")
        return False
    
    logger.info("Starting simulation in background greenlet...")
    simulation_running = True
    simulation_greenlet = eventlet.spawn(run_simulation_async)
    logger.info("Simulation greenlet spawned")
    return True


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'service': 'simulation',
        'simulation_active': simulation_running
    })


@app.route('/status')
def status():
    """Get simulation status."""
    bot_state = get_bot_state_safe()
    return jsonify({
        'simulation_running': simulation_running,
        'bot_state': {
            'running': bot_state.get('running', False),
            'mode': bot_state.get('mode'),
            'selected_coin': bot_state.get('selected_coin'),
            'balance': bot_state.get('balance', {})
        }
    })


@app.route('/health')
def health():
    """Health check for systemd or monitoring."""
    return jsonify({'status': 'healthy', 'simulation_running': simulation_running}), 200


# Start simulation immediately when the module is loaded
# This ensures the simulation starts even if no HTTP request is received
def init_on_startup():
    """Initialize simulation on startup."""
    logger.info("Auto-starting simulation on service startup...")
    # Use eventlet.spawn_after to delay startup slightly
    eventlet.spawn_after(2, start_simulation)


# Auto-start the simulation
init_on_startup()


# WSGI application object for Gunicorn
application = app


if __name__ == '__main__':
    # This should not be run directly - use gunicorn instead
    print("This is a WSGI entry point for the simulation service.")
    print("Use gunicorn to run the application:")
    print("  gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application")
    
    # For development, you can run with Flask's built-in server
    import sys
    if '--dev' in sys.argv:
        logger.info("Running in development mode...")
        start_simulation()
        app.run(host='0.0.0.0', port=5001, debug=False)

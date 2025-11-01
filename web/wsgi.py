"""
WSGI entry point for Gunicorn production server.

This module provides the WSGI application object for running Flask-SocketIO
with Gunicorn using eventlet workers.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import Flask app and SocketIO instance
from web.app import app, socketio
from utils.shared_state import set_socketio_instance

# Ensure socketio instance is set in shared_state (for WebSocket emits)
# This is already done in app.py, but we ensure it here as well
set_socketio_instance(socketio)

# WSGI application object for Gunicorn
# For Flask-SocketIO with eventlet workers, socketio.WSGIApp wraps the Flask app
application = socketio.WSGIApp(socketio, app)

if __name__ == '__main__':
    # This should not be run directly - use gunicorn instead
    print("This is a WSGI entry point. Use gunicorn to run the application.")
    print("Example: gunicorn -c web/gunicorn.conf.py web.wsgi:application")

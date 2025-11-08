"""
Gunicorn configuration file for Trading LLM Bot Dashboard Flask-SocketIO application.

This configuration uses eventlet workers which are required for Flask-SocketIO
WebSocket functionality.
"""

import multiprocessing
import os

# Server socket
bind = os.getenv('BIND', '0.0.0.0:5000')
backlog = 2048

# Worker processes
# With eventlet workers, a single worker can handle many concurrent connections
# due to green threading. Set to 1 worker for simpler deployment.
# You can override this with WORKERS environment variable if needed.
workers = int(os.getenv('WORKERS', 1))
worker_class = 'eventlet'  # Required for Flask-SocketIO
worker_connections = 1000  # Number of concurrent connections per worker
timeout = 120  # Seconds for worker timeout (longer for WebSocket connections)
keepalive = 5  # Seconds to wait for requests on Keep-Alive connection
graceful_timeout = 30  # Seconds to wait for graceful worker restart

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = os.getenv('ACCESS_LOG', 'logs/gunicorn_access.log')
errorlog = os.getenv('ERROR_LOG', 'logs/gunicorn_error.log')
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'trading_llm_bot_dashboard'

# Server mechanics
daemon = False
pidfile = os.getenv('PID_FILE', 'logs/gunicorn.pid')
umask = 0o007
user = None  # Set to username if running as different user
group = None  # Set to group name if running as different group
tmp_upload_dir = None

# SSL (if needed - uncomment and configure)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Preload application for better performance
# Disabled to fix eventlet RLock greening issues
# With preload_app=True, locks are created before eventlet monkey-patches threading
preload_app = False

# Worker initialization
def on_starting(server):
    """Called just before the master process is initialized."""
    # Ensure log directory exists
    log_dir = os.path.dirname(accesslog) if accesslog != '-' else os.path.dirname(errorlog)
    if log_dir and log_dir != '.':
        os.makedirs(log_dir, exist_ok=True)

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Trading LLM Bot Dashboard server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives INT or QUIT signal."""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application.
    
    This is called after eventlet has monkey-patched threading,
    so we can safely reinitialize locks here.
    """
    # Reset locks in shared_state after eventlet monkey-patching
    # This ensures locks are properly "greened" for eventlet
    try:
        from utils.shared_state import reset_lock
        reset_lock()
        worker.log.info("Reset locks after eventlet monkey-patching")
    except Exception as e:
        worker.log.warning(f"Failed to reset locks: {e}")

def worker_abort(worker):
    """Called when a worker times out."""
    worker.log.info("worker timed out")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down: Trading LLM Bot Dashboard")


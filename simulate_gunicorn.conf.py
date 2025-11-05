"""
Gunicorn configuration file for the Simulation Service.

This configuration uses eventlet workers to run the simulation continuously
in the background while providing a simple HTTP interface for health checks.
"""

import os

# Server socket - use a different port than the main web dashboard
bind = os.getenv('SIMULATION_BIND', '0.0.0.0:5001')
backlog = 512

# Worker processes
# Use a single worker for the simulation to avoid running multiple simulations
workers = 1
worker_class = 'eventlet'  # Required for async simulation
worker_connections = 100   # Lower than web service since this is just for monitoring
timeout = 300  # Longer timeout for simulation operations
keepalive = 5
graceful_timeout = 60  # Allow time for simulation to save state on shutdown

# Don't restart workers automatically - we want the simulation to run continuously
max_requests = 0  # Disable automatic worker restart
max_requests_jitter = 0

# Logging
accesslog = os.getenv('SIMULATION_ACCESS_LOG', 'logs/simulation_access.log')
errorlog = os.getenv('SIMULATION_ERROR_LOG', 'logs/simulation_error.log')
loglevel = os.getenv('SIMULATION_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'trading-llm-bot-simulation'

# Server mechanics
daemon = False
pidfile = os.getenv('SIMULATION_PID_FILE', 'logs/simulation.pid')
umask = 0o007
user = None
group = None

# Do not preload the app - let eventlet monkey-patch first
preload_app = False


# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    # Ensure log directory exists
    log_dir = os.path.dirname(accesslog) if accesslog != '-' else os.path.dirname(errorlog)
    if log_dir and log_dir != '.':
        os.makedirs(log_dir, exist_ok=True)
    server.log.info("Starting Simulation Service...")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Simulation Service is ready")


def worker_int(worker):
    """Called when a worker receives INT or QUIT signal."""
    worker.log.info("Simulation worker received INT or QUIT signal - shutting down gracefully")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Simulation worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Simulation worker initialized - simulation will start automatically")


def worker_abort(worker):
    """Called when a worker times out."""
    worker.log.warning("Simulation worker timed out")


def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Simulation Service")

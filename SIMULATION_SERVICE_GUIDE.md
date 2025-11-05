# Trading LLM Bot Simulation Service Guide

This guide explains how to run the trading simulation as a background service using Gunicorn and systemd, so you don't need to keep an SSH session open.

## Overview

The simulation service runs as a systemd service, similar to the web dashboard. It uses Gunicorn with eventlet workers to run the simulation continuously in the background.

## Features

? Runs simulation as a background service (no SSH session needed)
? Automatic restart on failure
? System logging with journald
? HTTP health check endpoints
? Configurable to trade BTC or SOL
? Integrated with existing shared state for dashboard visibility

## Quick Start

### 1. Set Default Coin to BTC

The `.env` file has been updated to use BTC by default:

```bash
DEFAULT_COIN=BTC
INITIAL_BALANCE_USDT=1000
INITIAL_BALANCE_SOL=10
INITIAL_BALANCE_BTC=0.01
```

You can modify these values in `.env` to change the default behavior.

### 2. Install the Service

Run the setup script:

```bash
cd /home/cali/trading_llm_bot
./scripts/setup_simulation_service.sh
```

The script will:
- Verify all required files exist
- Create the systemd service with your user/group
- Ask if you want to enable and start the service immediately

### 3. Service Management

**Start the service:**
```bash
sudo systemctl start trading_llm_bot.service
```

**Stop the service:**
```bash
sudo systemctl stop trading_llm_bot.service
```

**Restart the service:**
```bash
sudo systemctl restart trading_llm_bot.service
```

**Enable on boot:**
```bash
sudo systemctl enable trading_llm_bot.service
```

**Check status:**
```bash
sudo systemctl status trading_llm_bot.service
```

### 4. View Logs

**Real-time system logs:**
```bash
sudo journalctl -u trading_llm_bot.service -f
```

**Application logs:**
```bash
tail -f logs/simulation_error.log
tail -f simulate_service.log
```

**Access logs:**
```bash
tail -f logs/simulation_access.log
```

## HTTP Endpoints

The simulation service provides simple HTTP endpoints for monitoring:

**Health Check:**
```bash
curl http://localhost:5001/health
```

**Detailed Status:**
```bash
curl http://localhost:5001/status
```

**Root Endpoint:**
```bash
curl http://localhost:5001/
```

## Switching Between BTC and SOL

### Method 1: Change Default in .env (Recommended)

Edit `.env` and change:
```bash
DEFAULT_COIN=BTC  # or SOL
```

Then restart the service:
```bash
sudo systemctl restart trading_llm_bot.service
```

### Method 2: Command Line Override

If you want to run manually with a different coin:
```bash
source venv/bin/activate
python simulate.py --coin BTC
```

### Method 3: Environment Variable Override

Set the environment variable before starting:
```bash
sudo systemctl stop trading_llm_bot.service
sudo systemctl edit trading_llm_bot.service
```

Add:
```ini
[Service]
Environment="DEFAULT_COIN=BTC"
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start trading_llm_bot.service
```

## Architecture

### Files Created

1. **`simulate_wsgi.py`** - WSGI wrapper that runs simulation in background greenlet
2. **`simulate_gunicorn.conf.py`** - Gunicorn configuration for simulation service
3. **`trading_llm_bot.service`** - Systemd service definition
4. **`scripts/setup_simulation_service.sh`** - Installation script

### How It Works

1. Gunicorn starts with eventlet workers
2. The WSGI application (`simulate_wsgi.py`) initializes a Flask app
3. On startup, it spawns a background eventlet greenlet
4. The greenlet runs the simulation asynchronously
5. HTTP endpoints provide monitoring and health checks
6. Systemd ensures the service restarts on failure

### Port Configuration

- **Main Dashboard**: Port 5000 (web.wsgi)
- **Simulation Service**: Port 5001 (simulate_wsgi)

You can change the simulation port by setting the `SIMULATION_BIND` environment variable:
```bash
export SIMULATION_BIND="0.0.0.0:5002"
```

## Integration with Dashboard

The simulation service uses the same shared state as the web dashboard, so:
- The dashboard will show the simulation status
- Trades and balance updates are visible on the dashboard
- Both services can run simultaneously

## Troubleshooting

### Service Won't Start

Check logs:
```bash
sudo journalctl -u trading_llm_bot.service -n 50 --no-pager
```

### Simulation Not Trading

1. Check if the simulation is actually running:
```bash
curl http://localhost:5001/status | python -m json.tool
```

2. Verify the coin configuration:
```bash
grep DEFAULT_COIN .env
```

3. Check the application logs:
```bash
tail -100 simulate_service.log
```

### Port Already in Use

If port 5001 is in use, change the bind address in `simulate_gunicorn.conf.py`:
```python
bind = os.getenv('SIMULATION_BIND', '0.0.0.0:5002')
```

### Permission Issues

Ensure the service runs as your user:
```bash
sudo systemctl cat trading_llm_bot.service | grep User=
```

Should show your username.

## Running Both Services

You can run both the web dashboard and simulation service simultaneously:

```bash
# Start web dashboard
sudo systemctl start solbot.service

# Start simulation
sudo systemctl start trading_llm_bot.service

# Check both are running
sudo systemctl status solbot.service
sudo systemctl status trading_llm_bot.service
```

## Manual Testing (Development)

For testing without systemd:

```bash
source venv/bin/activate
gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application
```

Or with Flask's dev server:
```bash
python simulate_wsgi.py --dev
```

## Benefits Over SSH Session

? **No SSH session required** - Service runs independently
? **Automatic restart** - If it crashes, systemd restarts it
? **Survives logout** - Keeps running when you disconnect
? **System integration** - Managed like any other system service
? **Proper logging** - Integrated with system logs
? **Clean shutdown** - Graceful handling of stop/restart signals

## Next Steps

1. Run the setup script to install the service
2. Monitor the logs to ensure it's working
3. Check the dashboard to see simulation data
4. Adjust trading parameters in `.env` as needed

## Support

If you encounter issues:
1. Check the logs (journalctl and application logs)
2. Verify the configuration in `.env`
3. Ensure the virtual environment has all dependencies
4. Test manually before using systemd

---

**Happy Trading! ??**

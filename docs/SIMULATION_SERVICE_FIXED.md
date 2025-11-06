# Simulation Service - Fixed and Running ?

**Date**: November 5, 2025  
**Status**: ? **OPERATIONAL**

## What Was Fixed

### Issue 1: Flask `before_first_request` Deprecated
- **Problem**: Flask 2.3+ removed the `@app.before_first_request` decorator
- **Error**: `AttributeError: 'Flask' object has no attribute 'before_first_request'`
- **Fix**: Removed the deprecated decorator and kept only the `init_on_startup()` function that uses `eventlet.spawn_after()`

### Issue 2: Service Not Starting
- **Problem**: Service was failing with exit code 3 (NOTIMPLEMENTED)
- **Fix**: Updated `simulate_wsgi.py` to work with Flask 2.3+

## Current Status

### ? Service Running
```bash
sudo systemctl status trading_llm_bot.service
```

**Output**:
- Status: **active (running)**
- PID: 110704 (master), 110706 (worker)
- Port: **5001**
- Worker: eventlet (async simulation)

### ? Simulation Active
```bash
curl http://localhost:5001/status
```

**Current Portfolio**:
- USDT: $1,000.00
- SOL: 10.0 @ $161.98 = $1,619.80
- BTC: 0.01 @ $103,700.10 = $1,037.00
- **Total Portfolio**: $3,656.80

### ? Real-time Updates
- WebSocket connected to Kraken
- Receiving live price updates for BTC and SOL
- LLM advisor actively analyzing market conditions
- Technical indicators calculating (RSI, MACD, ADX, etc.)

## Service Management

### Start Service
```bash
sudo systemctl start trading_llm_bot.service
```

### Stop Service
```bash
sudo systemctl stop trading_llm_bot.service
```

### Restart Service
```bash
sudo systemctl restart trading_llm_bot.service
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u trading_llm_bot.service -f

# Last 50 lines
sudo journalctl -u trading_llm_bot.service -n 50
```

### Check Status
```bash
# Service status
sudo systemctl status trading_llm_bot.service

# Simulation status via API
curl http://localhost:5001/status

# Health check
curl http://localhost:5001/health
```

## Service Configuration

### Service File
**Location**: `/etc/systemd/system/trading_llm_bot.service`

**Key Settings**:
- User: `cali`
- Working Directory: `/home/cali/trading_llm_bot`
- Command: `gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application`
- Port: `5001`
- Restart: `always` (auto-restart on failure)
- Logging: systemd journal + logs/

### Gunicorn Configuration
**File**: `simulate_gunicorn.conf.py`

**Key Settings**:
- Workers: 1 (single simulation instance)
- Worker Class: `eventlet` (async support)
- Bind: `0.0.0.0:5001`
- Timeout: 300 seconds
- Access Log: `logs/simulation_access.log`
- Error Log: `logs/simulation_error.log`

## API Endpoints

### Health Check
```bash
curl http://localhost:5001/health
```
Returns: `{"status": "healthy", "simulation_running": true}`

### Status
```bash
curl http://localhost:5001/status
```
Returns: Full simulation state including:
- Bot running status
- Current balances (USDT, SOL, BTC)
- Technical indicators
- Price data
- Historical data

### Root
```bash
curl http://localhost:5001/
```
Returns: Basic service info

## Architecture

```
trading_llm_bot.service (systemd)
    ??? gunicorn (master process)
        ??? eventlet worker
            ??? Flask app (HTTP endpoints on :5001)
            ??? Simulation greenlet (background)
                ??? WebSocket connection (Kraken)
                ??? Data fetchers (prices, history)
                ??? Technical indicators
                ??? ML models
                ??? LLM advisor
                ??? Trading logic
```

## Important Notes

1. **Single Worker**: The service uses only 1 worker to ensure a single simulation instance runs
2. **Eventlet**: Uses eventlet for async/concurrent operations
3. **Auto-start**: Simulation starts automatically 2 seconds after worker initialization
4. **Persistent**: Service is enabled to start on boot
5. **Shared State**: Simulation data is available to the main dashboard via shared state

## Related Services

### Main Web Dashboard
- Service: `web/gunicorn` (PID 109002, 109027)
- Port: **5000**
- URL: http://localhost:5000

### Processes Running
```
cali  109002  /home/cali/solbot/venv/bin/python3 /home/cali/trading_llm_bot/venv/bin/gunicorn -c web/gunicorn.conf.py web.wsgi:application
cali  109027  /home/cali/solbot/venv/bin/python3 /home/cali/trading_llm_bot/venv/bin/gunicorn -c web/gunicorn.conf.py web.wsgi:application
cali  110704  /home/cali/solbot/venv/bin/python3 /home/cali/trading_llm_bot/venv/bin/gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application
cali  110706  /home/cali/solbot/venv/bin/python3 /home/cali/trading_llm_bot/venv/bin/gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application
```

## Files Modified

1. **simulate_wsgi.py**
   - Removed deprecated `@app.before_first_request` decorator
   - Kept `init_on_startup()` function for automatic simulation start

## Next Steps

1. ? Service is running and stable
2. ? Auto-restart enabled
3. ? Enabled on boot
4. Monitor logs for trading activity
5. Access dashboard at http://localhost:5000 to view simulation

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u trading_llm_bot.service -n 50

# Test config manually
cd /home/cali/trading_llm_bot
/home/cali/trading_llm_bot/venv/bin/gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application --check-config
```

### Simulation Not Running
```bash
# Check if greenlet spawned
curl http://localhost:5001/status | grep simulation_running

# If false, restart service
sudo systemctl restart trading_llm_bot.service
```

### Port Already in Use
```bash
# Check what's using port 5001
sudo lsof -i :5001

# Kill conflicting process
sudo kill <PID>
```

---

**? The simulation service is now fully operational and will run continuously!**

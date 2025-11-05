# Simulation Not Visible on Dashboard - Quick Fix

## Problem

Simulation is running and making trades, but the web dashboard shows nothing because shared state isn't updated.

## Quick Fix

The simulation needs to update the shared state. Here's what to do:

### Option 1: Restart Simulation Service (Recommended)

```bash
# Stop the systemd service
sudo systemctl stop solbot-simulation

# Start it again - this will properly initialize shared state
sudo systemctl start solbot-simulation

# Check it's running
sudo systemctl status solbot-simulation

# View logs to confirm trades
sudo journalctl -u solbot-simulation -f
```

After restarting, the dashboard should show:
- `running: true`
- Current balance
- Trade activity

### Option 2: Start Through Web Interface

1. Stop the systemd service first:
   ```bash
   sudo systemctl stop solbot-simulation
   ```

2. Go to web dashboard: `http://your-server:5000`
3. Click "Start Simulation"
4. The dashboard will now show the simulation

### Option 3: Manually Update State (Temporary)

```bash
python -c "from utils.shared_state import update_bot_state_safe; update_bot_state_safe({'running': True, 'mode': 'simulation'})"
```

This is temporary - restart the service for a permanent fix.

## Why This Happens

The systemd service runs in a separate process. When it starts:
1. It should set `running: True` in shared state (now fixed in code)
2. But if started before the fix, it might not have set it
3. The trading loop updates state every cycle, but if `running` was never set initially, it might not show

## Verification

After restarting, check:
```bash
# Check shared state
python -c "from utils.shared_state import get_bot_state_safe; print(get_bot_state_safe().get('running'))"
# Should show: True

# Check web API
curl http://localhost:5000/get_status | python -m json.tool | grep running
# Should show: "running": true
```

## Current Status

? **Simulation IS running** (systemd service, PID 28914)
? **Trades ARE happening** (see logs - "Trade action: buy/sell")
? **Fix is applied** (trading loop now keeps `running: True`)
? **Dashboard can't see it** (needs restart to initialize state)

**Solution**: Restart the simulation service to properly initialize shared state.

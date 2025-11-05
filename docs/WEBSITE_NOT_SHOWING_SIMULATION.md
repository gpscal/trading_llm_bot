# Website Not Showing Simulation - Fix Guide

## Problem

The simulation is running in the background, but the website dashboard shows nothing.

## Root Cause

The shared state had `running: false`, which makes the web dashboard think nothing is running, even though the simulation process is active.

## Solutions

### Quick Fix (Temporary)

```bash
python -c "from utils.shared_state import update_bot_state_safe; update_bot_state_safe({'running': True, 'mode': 'simulation'})"
```

This manually sets the state to show simulation is running.

### Permanent Fix

**Restart the simulation through the web interface:**

1. Go to your web dashboard
2. Click "Stop" (to clean up old state)
3. Click "Start Simulation" with your desired balances

This ensures:
- State is properly initialized
- WebSocket connections work
- Dashboard updates in real-time

### Check Status

```bash
# Check if simulation process is running
ps aux | grep simulate.py

# Check shared state
python -c "from utils.shared_state import get_bot_state_safe; import json; print(json.dumps(get_bot_state_safe(), indent=2, default=str))"

# Check recent logs
tail -50 simulate.log
```

## Why This Happened

The simulation was likely started directly (not through web interface), so:
1. State wasn't initialized with `running: True`
2. WebSocket connections weren't established
3. Dashboard couldn't see the simulation

## Prevention

**Always start simulations through the web interface** for proper state management and real-time updates.

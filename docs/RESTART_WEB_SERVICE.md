# Restart Web Service - Quick Fix

## The Issue

Your website is disconnected because:
1. Systemd simulation service is running in a separate process
2. Web workers haven't reloaded the updated code
3. Shared state isn't being synced

## Quick Fix

**Restart the web service to load the updated code:**

```bash
sudo systemctl restart solbot
```

Or if you don't have sudo passwordless access:

```bash
# Stop old workers
pkill -HUP -f "gunicorn.*wsgi"

# Or full restart
sudo systemctl restart solbot
```

## After Restart

1. **Wait 5-10 seconds** for service to start
2. **Refresh your browser** at `http://your-server:5000`
3. **Check status**: The website should now:
   - Detect systemd simulation service
   - Show `running: true` if simulation is active
   - Allow you to start/stop from web interface

## Verify It's Working

```bash
# Check status endpoint
curl http://localhost:5000/get_status | python -m json.tool | grep -E "running|mode|systemd"
```

Should show:
```json
"running": true,
"mode": "simulation",
"systemd_running": true
```

## If Still Not Working

1. Check web service logs:
   ```bash
   tail -f logs/gunicorn_error.log
   ```

2. Check if web service is running:
   ```bash
   systemctl status solbot
   ```

3. Try accessing directly:
   ```bash
   curl http://localhost:5000/
   ```

## Alternative: Use Web Interface Only

If you prefer to control everything from the web:

```bash
# Stop systemd service
sudo systemctl stop solbot-simulation

# Restart web service
sudo systemctl restart solbot

# Now use web interface to start simulation
```

This way, everything is managed from one place!

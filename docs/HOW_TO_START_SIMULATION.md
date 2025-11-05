# How to Start SolBot Simulation

## Current Setup

Your `solbot.service` only runs the **web server** (Flask/Gunicorn), NOT the simulation.

The simulation must be started separately.

## Option 1: Start Through Web Interface (Recommended for Testing)

1. **Access your web dashboard**: `http://your-server-ip:5000`
2. **Click "Start Simulation"** button
3. The simulation will run as a thread in the web server process

**Note**: If you restart `solbot.service`, any running simulation will stop.

## Option 2: Create Separate Systemd Service (Recommended for Production)

Create a dedicated service that runs the simulation independently:

```bash
sudo bash scripts/create_solbot_simulation_service.sh
```

Then:
```bash
# Start the simulation service
sudo systemctl start solbot-simulation

# Enable to start on boot
sudo systemctl enable solbot-simulation

# Check status
sudo systemctl status solbot-simulation

# View logs
sudo journalctl -u solbot-simulation -f
```

**Benefits**:
- Simulation runs independently of web server
- Auto-restarts if it crashes
- Survives web server restarts
- Can start on system boot

## Option 3: Start Manually (For Development)

```bash
cd /home/cali/solbot
source venv/bin/activate
python simulate.py
```

This runs in foreground - good for debugging.

## Which Service Does What?

- **`solbot.service`**: Runs web server (Flask/Gunicorn) on port 5000
- **`solbot-simulation.service`** (if created): Runs trading simulation
- **Web Interface**: Can start/stop simulation as threads (not persistent)

## Recommended Setup

For production, use **Option 2**:
1. `solbot.service` - Web dashboard (always running)
2. `solbot-simulation.service` - Trading simulation (runs independently)

This way:
- Web server can restart without affecting simulation
- Simulation can restart without affecting web server
- Both are managed by systemd
- Both auto-restart on failure

## Current Status

Check what's running:
```bash
# Web server status
sudo systemctl status solbot

# Simulation status (if service exists)
sudo systemctl status solbot-simulation

# Check processes
ps aux | grep -E "gunicorn|simulate"
```

## Troubleshooting

### Web server not responding
```bash
sudo systemctl restart solbot
sudo journalctl -u solbot -n 50
```

### Simulation not running
1. Check if started through web interface (thread) or service
2. Start it through web dashboard or create the service
3. Check logs: `tail -f simulate.log`

### Simulation started but website shows nothing
- Check shared state: `python -c "from utils.shared_state import get_bot_state_safe; print(get_bot_state_safe()['running'])"`
- Restart through web interface to properly initialize state

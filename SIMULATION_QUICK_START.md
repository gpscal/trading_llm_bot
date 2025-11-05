# Simulation Service - Quick Reference

## ? Current Status: RUNNING

### Quick Check
```bash
# Check if running
systemctl is-active trading_llm_bot.service

# Health check
curl http://localhost:5001/health
```

## Service Control

### Start
```bash
sudo systemctl start trading_llm_bot.service
```

### Stop
```bash
sudo systemctl stop trading_llm_bot.service
```

### Restart
```bash
sudo systemctl restart trading_llm_bot.service
```

### Status
```bash
sudo systemctl status trading_llm_bot.service
```

## View Logs

### Real-time (live tail)
```bash
sudo journalctl -u trading_llm_bot.service -f
```

### Last 50 lines
```bash
sudo journalctl -u trading_llm_bot.service -n 50
```

### Since today
```bash
sudo journalctl -u trading_llm_bot.service --since today
```

## API Endpoints

### Port: 5001

```bash
# Health check
curl http://localhost:5001/health

# Full status with balance
curl http://localhost:5001/status

# Service info
curl http://localhost:5001/
```

## Dashboard

**Main Dashboard**: http://localhost:5000 (port 5000)  
**Simulation API**: http://localhost:5001 (port 5001)

## Current Trading

- **Coin**: BTC (Bitcoin)
- **USDT**: $1,000.00
- **SOL**: 10.0 @ $161.98
- **BTC**: 0.01 @ $103,700.10
- **Total**: $3,656.80

## What's Running

1. **WebSocket**: Connected to Kraken for live prices
2. **Data Fetchers**: Polling historical data
3. **Technical Indicators**: RSI, MACD, ADX, Bollinger Bands, etc.
4. **ML Models**: Profitability prediction
5. **LLM Advisor**: Market analysis with Ollama
6. **Trading Logic**: Automated buy/sell decisions

## Service Details

- **Auto-start on boot**: ? Enabled
- **Auto-restart on failure**: ? Enabled
- **Working Directory**: `/home/cali/trading_llm_bot`
- **User**: `cali`
- **Port**: `5001`

## Troubleshooting

### Service won't start?
```bash
# Check error logs
sudo journalctl -u trading_llm_bot.service -n 100

# Test manually
cd /home/cali/trading_llm_bot
./venv/bin/gunicorn -c simulate_gunicorn.conf.py simulate_wsgi:application
```

### Port already in use?
```bash
# Find what's using port 5001
sudo lsof -i :5001

# Stop service and kill any strays
sudo systemctl stop trading_llm_bot.service
sudo pkill -f "simulate_gunicorn"
```

### Simulation not visible?
```bash
# Check if simulation is running
curl http://localhost:5001/status | grep simulation_running

# Should return: "simulation_running": true
```

## Files

- **Service**: `/etc/systemd/system/trading_llm_bot.service`
- **WSGI**: `simulate_wsgi.py`
- **Config**: `simulate_gunicorn.conf.py`
- **Logs**: `logs/simulation_access.log`, `logs/simulation_error.log`

---

**Everything is working! The simulation is running 24/7.** ??

# SolBot

SolBot is a SOL trading bot that uses various market indicators and strategies to make trading decisions on the Kraken exchange. The bot is built using Python and leverages asynchronous programming to handle real-time data from the Kraken WebSocket API.

## Features

- **Real-time Data:** Utilizes Kraken's WebSocket API for real-time market data.
- **Technical Indicators:** Implements multiple technical indicators like MACD, RSI, Moving Average, Bollinger Bands, and more.
- **Dynamic Trading Strategy:** Adjusts trading actions based on a calculated confidence level from multiple indicators.
- **Logging:** Comprehensive logging of all trades and events for analysis and debugging.
- **Configurable Parameters:** Easy configuration of bot parameters through a `config.py` file.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/m0dE/solbot.git
   cd solbot
   ```

2. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Environment Variables:**

   Create a `.env` file in the root directory and add your Kraken API credentials:

   ```env
   API_KEY=your_kraken_api_key
   API_SECRET=your_kraken_api_secret
   ```

## Configuration

All configurable parameters are stored in the `config/config.py` file. You can adjust initial balances, API endpoints, trading fees, and other parameters to suit your trading strategy.

## Running the Bot

### Simulate Trading

To simulate trading, run:

```bash
python simulate.py
```

### Live Trading

To start live trading, run:

```bash
python live_trade.py
```

### Dashboard + Control API

To launch the Flask control API and HTML dashboard together, run:

```bash
python start_services.py
```

Or run the Flask app directly:

```bash
python web/app.py
```

The dashboard will be available at `http://localhost:5000/` or `http://localhost:5000/dashboard`

Use `Ctrl+C` to stop; the script shuts down the service cleanly.

**Note:** The dashboard uses WebSockets for real-time updates. Make sure your browser supports WebSockets and that port 5000 is accessible.

## Production Deployment

### Running as a Systemd Service with Gunicorn

For production deployment, SolBot can be run as a systemd service using Gunicorn with eventlet workers (required for Flask-SocketIO WebSockets).

#### Prerequisites

- Gunicorn and eventlet are installed (included in `requirements.txt`)
- Virtual environment is set up and activated
- Root/sudo access for installing systemd service

#### Installation

1. **Install the service:**

   ```bash
   sudo ./scripts/install_service.sh
   ```

   This will:
   - Create log directories
   - Install the systemd service file
   - Configure the service for your user

2. **Start the service:**

   ```bash
   sudo systemctl start solbot
   ```

3. **Enable service to start on boot (optional):**

   ```bash
   sudo systemctl enable solbot
   ```

#### Service Management

- **Start service:**
  ```bash
  sudo systemctl start solbot
  ```

- **Stop service:**
  ```bash
  sudo systemctl stop solbot
  ```

- **Restart service:**
  ```bash
  sudo systemctl restart solbot
  ```

- **Check service status:**
  ```bash
  sudo systemctl status solbot
  ```

- **View logs:**
  ```bash
  # Systemd journal logs
  sudo journalctl -u solbot -f
  
  # Gunicorn access logs
  tail -f logs/gunicorn_access.log
  
  # Gunicorn error logs
  tail -f logs/gunicorn_error.log
  ```

- **Reload service (graceful restart):**
  ```bash
  sudo systemctl reload solbot
  ```

#### Uninstallation

To remove the service:

```bash
sudo ./scripts/uninstall_service.sh
```

#### Configuration

Gunicorn configuration can be customized in `web/gunicorn.conf.py`. Key settings:

- **Workers:** Number of worker processes (default: CPU cores * 2 + 1)
- **Bind address:** Set via `BIND` environment variable (default: `0.0.0.0:5000`)
- **Logging:** Configure log paths via `ACCESS_LOG` and `ERROR_LOG` environment variables
- **Worker timeout:** Set to 120 seconds for WebSocket connections

Environment variables can be set in the systemd service file or via `.env` file.

#### Troubleshooting

- **Service won't start:** Check logs with `sudo journalctl -u solbot -n 50`
- **WebSocket not working:** Ensure eventlet workers are being used (check gunicorn config)
- **Permission errors:** Ensure log directory is writable by the service user
- **Port already in use:** Change bind address in `gunicorn.conf.py` or systemd service file

#### Manual Gunicorn Execution

You can also run Gunicorn manually (for testing):

```bash
# From project root, with venv activated
gunicorn -c web/gunicorn.conf.py web.wsgi:application
```

## Project Structure

```
solbot/
├── api/
│   ├── __init__.py
│   ├── kraken.py
│   └── websocket.py
├── config/
│   └── config.py
├── strategies/
│   └── indicators/
│       ├── __init__.py
│       ├── calculate_indicators.py
│       └── [various indicator modules]
├── trade/
│   ├── __init__.py
│   ├── trade_logic.py
│   └── volume_calculator.py
├── utils/
│   ├── __init__.py
│   ├── balance.py
│   ├── logger.py
│   ├── periodic_tasks.py
│   ├── trade_utils.py
│   ├── shared_state.py
│   └── websocket_handler.py
├── web/
│   ├── app.py
│   ├── wsgi.py
│   ├── gunicorn.conf.py
│   ├── templates/
│   │   └── dashboard.html
│   └── static/
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           └── dashboard.js
├── scripts/
│   ├── install_service.sh
│   └── uninstall_service.sh
├── logs/
│   ├── gunicorn_access.log
│   └── gunicorn_error.log
├── solbot.service
├── .env
├── .gitignore
├── index.py
├── live_trade.py
├── requirements.txt
├── simulate.py
├── start_services.py
└── test_req.py
```

## Technical Indicators

SolBot uses the following technical indicators:

- **MACD (Moving Average Convergence Divergence)**
- **RSI (Relative Strength Index)**
- **Moving Average**
- **Bollinger Bands**
- **ATR (Average True Range)**
- **Stochastic Oscillator**

## Contribution

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. The bot is provided as-is and should be used at your own risk. Always do your own research before making any trading decisions.

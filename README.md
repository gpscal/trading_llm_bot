# Trading LLM Bot

An advanced AI-powered cryptocurrency trading bot that combines traditional technical analysis with cutting-edge LLM (Large Language Model) intelligence for automated trading on Kraken. Originally designed for Solana (SOL) trading, the bot has evolved to support multi-coin trading including Bitcoin (BTC) and Solana (SOL).

## 🚀 Key Features

### AI-Powered Trading
- **LLM Advisor Integration:** Leverages AI language models for intelligent trading signals and decision-making
- **Deep Market Analyzer:** Comprehensive market analysis using Claude AI with RAG (Retrieval-Augmented Generation)
- **Machine Learning Models:** Price prediction and profitability forecasting using PyTorch
- **News Sentiment Analysis:** Real-time cryptocurrency news analysis from CryptoCompare and NewsAPI.ai

### Multi-Coin Support
- **Trading Pairs:** BTC/USD, SOL/USD (easily extensible to other coins)
- **Exchange:** Kraken (only supported exchange)
- **Real-time Data:** WebSocket connections for live market data streaming
- **REST API Integration:** Fallback and historical data fetching

### Advanced Technical Analysis
- **Technical Indicators:** MACD, RSI, Moving Averages, Bollinger Bands, ATR, Stochastic Oscillator, ADX, OBV, and more
- **Dynamic Strategy:** Multi-factor confidence scoring system that weighs various indicators
- **Support & Resistance:** Automatic detection of key price levels
- **Divergence Detection:** Identifies bullish and bearish divergences

### Risk Management
- **Stop Loss:** Configurable percentage-based stop losses
- **Trailing Stop:** Dynamic trailing stops to protect profits
- **Take Profit Targets:** Multiple take-profit levels
- **Max Drawdown Protection:** Portfolio-level risk controls
- **Position Sizing:** Intelligent volume calculation based on confidence levels

### Real-Time Monitoring
- **Web Dashboard:** Beautiful, responsive HTML/CSS/JavaScript dashboard with live updates
- **WebSocket Integration:** Real-time trade notifications and status updates
- **Discord Notifications:** Real-time alerts and trade notifications via Discord
- **Comprehensive Logging:** Detailed logs for all operations, trades, and system events

### Production-Ready
- **Systemd Services:** Run as background services on Linux
- **Gunicorn + Eventlet:** Production-grade WSGI server with WebSocket support
- **Live & Simulation Modes:** Test strategies without risking real funds
- **Configurable Parameters:** Extensive configuration through environment variables and config files

## Installation

1. **Clone the Repository:**

   ```bash
   git clone 
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

   Create a `.env` file in the root directory with the following variables:

   ```env
   # Kraken API Credentials (only supported exchange)
   API_KEY=your_kraken_api_key
   API_SECRET=your_kraken_api_secret
   
   # AI/LLM Configuration
   ANTHROPIC_API_KEY=your_anthropic_api_key  # For Claude AI
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # Claude model
   OPENROUTER_API_KEY=your_openrouter_key  # Fallback LLM provider
   OLLAMA_BASE_URL=http://localhost:11434  # Local Ollama instance
   OLLAMA_MODEL=deepseek-r1:8b  # Fast LLM model
   
   # News APIs
   CRYPTOCOMPARE_API_KEY=your_cryptocompare_key  # Primary news source
   NEWS_API_AI=your_newsapi_key  # Fallback news source
   
   # Discord Notifications (only notification service)
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id
   
   # Trading Configuration
   DEFAULT_COIN=SOL  # Default coin to trade (SOL or BTC)
   INITIAL_BALANCE_USDT=1000
   INITIAL_BALANCE_SOL=10
   INITIAL_BALANCE_BTC=0.01
   MIN_VOLUME_SOL=0.1
   MAX_VOLUME_SOL=10
   MIN_VOLUME_BTC=0.0001
   MAX_VOLUME_BTC=0.25
   ```

## Configuration

All configurable parameters are stored in the `config/config.py` file. You can adjust initial balances, API endpoints, trading fees, and other parameters to suit your trading strategy.

## Running the Bot

### Simulate Trading

Test your strategies risk-free with simulation mode:

```bash
# Simulate trading SOL (default)
python simulate.py

# Simulate trading BTC
python simulate.py --coin BTC

# Custom initial balances
python simulate.py --initial_balance_usdt 5000 --initial_balance_sol 20 --coin SOL
```

### Live Trading

Start live trading with real funds:

```bash
# Live trade SOL (default)
python live_trade.py

# Live trade BTC
python live_trade.py --coin BTC
```

**⚠️ WARNING:** Live trading uses real funds. Always test with simulation mode first!

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

For production deployment, Trading LLM Bot can be run as a systemd service using Gunicorn with eventlet workers (required for Flask-SocketIO WebSockets).

The bot includes two systemd services:
- `trading_llm_bot_dashboard.service` - Web dashboard with real-time monitoring
- `trading_llm_bot_simulation.service` - Background trading simulation

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

2. **Start the services:**

   ```bash
   # Start dashboard service
   sudo systemctl start trading_llm_bot_dashboard
   
   # Start simulation service
   systemctl --user start trading_llm_bot_simulation
   ```

3. **Enable services to start on boot (optional):**

   ```bash
   sudo systemctl enable trading_llm_bot_dashboard
   systemctl --user enable trading_llm_bot_simulation
   ```

#### Service Management

- **Dashboard Service (system-wide):**
  ```bash
  # Start/stop/restart
  sudo systemctl start trading_llm_bot_dashboard
  sudo systemctl stop trading_llm_bot_dashboard
  sudo systemctl restart trading_llm_bot_dashboard
  
  # Check status
  sudo systemctl status trading_llm_bot_dashboard
  
  # View logs
  sudo journalctl -u trading_llm_bot_dashboard -f
  tail -f logs/gunicorn_access.log
  tail -f logs/gunicorn_error.log
  ```

- **Simulation Service (user-level):**
  ```bash
  # Start/stop/restart
  systemctl --user start trading_llm_bot_simulation
  systemctl --user stop trading_llm_bot_simulation
  systemctl --user restart trading_llm_bot_simulation
  
  # Check status
  systemctl --user status trading_llm_bot_simulation
  
  # View logs
  journalctl --user -u trading_llm_bot_simulation -f
  tail -f simulate.log
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

- **Service won't start:** Check logs with `sudo journalctl -u trading_llm_bot_dashboard -n 50`
- **WebSocket not working:** Ensure eventlet workers are being used (check `web/gunicorn.conf.py`)
- **Permission errors:** Ensure log directory is writable by the service user
- **Port already in use:** Change bind address in `gunicorn.conf.py` or systemd service file
- **LLM errors:** Verify API keys in `.env` file (ANTHROPIC_API_KEY, OPENROUTER_API_KEY)
- **Exchange connection issues:** Check API credentials and network connectivity

#### Manual Gunicorn Execution

You can also run Gunicorn manually (for testing):

```bash
# From project root, with venv activated
gunicorn -c web/gunicorn.conf.py web.wsgi:application
```

## Running Simulations with Laptop Lid Closed

When you close your laptop lid, Linux typically suspends the system, which will pause any running simulations. To prevent this and allow simulations to continue running:

### Option 1: Prevent System Suspend on Lid Close (Recommended)

This prevents the system from suspending when the lid is closed, allowing all processes (including simulations) to continue running:

```bash
sudo ./scripts/configure_lid_close.sh
```

This script:
- Configures systemd-logind to ignore lid close events
- Creates a backup of your current logind configuration
- Restarts the logind service to apply changes

**To revert:** Restore from the backup file created by the script.

### Option 2: Run Simulation as a Systemd User Service

Run simulations as a persistent service that survives disconnections:

1. **Create the service:**
   ```bash
   ./scripts/create_simulation_service.sh
   ```

2. **Start the simulation service:**
   ```bash
   systemctl --user start trading_llm_bot_simulation
   ```

3. **Enable it to start on login (optional):**
   ```bash
   systemctl --user enable trading_llm_bot_simulation
   ```

4. **Check status:**
   ```bash
   systemctl --user status trading_llm_bot_simulation
   ```

5. **View logs:**
   ```bash
   journalctl --user -u trading_llm_bot_simulation -f
   ```

6. **Stop the service:**
   ```bash
   systemctl --user stop trading_llm_bot_simulation
   ```

**Customizing simulation parameters:** Edit the service file at `~/.config/systemd/user/trading_llm_bot_simulation.service` and modify the `ExecStart` line, then run `systemctl --user daemon-reload`.

### Option 3: Use Screen or Tmux (Quick Alternative)

For a quick solution without modifying system settings:

```bash
# Using screen
screen -S trading-bot-sim
cd /home/cali/trading_llm_bot
source venv/bin/activate
python simulate.py
# Press Ctrl+A then D to detach

# To reattach later
screen -r trading-bot-sim
```

```bash
# Using tmux
tmux new -s trading-bot-sim
cd /home/cali/trading_llm_bot
source venv/bin/activate
python simulate.py
# Press Ctrl+B then D to detach

# To reattach later
tmux attach -t trading-bot-sim
```

**Note:** Options 1 and 2 work best together - configure logind to prevent suspend AND run as a service for maximum reliability.

## Project Structure

```
trading_llm_bot/
├── api/                              # Exchange API integrations
│   ├── kraken.py                     # Kraken exchange (only supported exchange)
│   └── websocket.py                  # WebSocket connections
├── config/
│   ├── config.py                     # Main configuration
│   └── config_gpu.py                 # GPU-accelerated ML config
├── strategies/
│   └── indicators/                   # Technical indicators library
│       ├── calculate_indicators.py
│       ├── macd.py, rsi.py, etc.
│       └── [20+ indicator modules]
├── ml/                               # Machine Learning models
│   ├── deep_analyzer.py              # Claude AI deep analysis
│   ├── price_predictor.py            # Price prediction model
│   └── profitability_predictor.py    # Trade outcome prediction
├── LLM_trader/                       # LLM Advisor integration
│   ├── core/                         # Core LLM trading logic
│   ├── indicators/                   # Extended indicator library
│   └── config/                       # LLM model configuration
├── trade/
│   ├── trade_logic.py                # Trading decision engine
│   └── volume_calculator.py          # Position sizing
├── utils/                            # Utility modules
│   ├── balance.py                    # Kraken balance management
│   ├── coin_pair_manager.py          # Trading pair mapping
│   ├── data_fetchers.py              # Historical data fetching
│   ├── trading_orchestrator.py       # Unified trading loop
│   ├── discord_notifier.py           # Discord notifications (only notification service)
│   └── [15+ utility modules]
├── web/                              # Web dashboard
│   ├── app.py                        # Flask application
│   ├── wsgi.py                       # WSGI entry point
│   ├── gunicorn.conf.py              # Production server config
│   ├── templates/
│   │   └── dashboard.html            # Real-time dashboard UI
│   └── static/
│       ├── css/dashboard.css
│       └── js/dashboard.js
├── scripts/                          # Installation scripts
│   ├── install_service.sh
│   ├── configure_lid_close.sh
│   └── [deployment scripts]
├── models/                           # Trained ML models
│   ├── price_predictor.pth
│   └── profitability_predictor.pth
├── logs/                             # Application logs
├── tests/                            # Test suite
├── trading_llm_bot_dashboard.service # Dashboard systemd service
├── trading_llm_bot_simulation.service # Simulation systemd service
├── .env                              # Environment variables
├── live_trade.py                     # Live trading entry point
├── simulate.py                       # Simulation entry point
├── start_services.py                 # Service orchestrator
└── requirements.txt                  # Python dependencies
```

## Technical Indicators & Analysis

Trading LLM Bot implements a comprehensive suite of technical indicators:

### Momentum Indicators
- **MACD (Moving Average Convergence Divergence)** - Trend following momentum
- **RSI (Relative Strength Index)** - Overbought/oversold conditions
- **Stochastic Oscillator** - Momentum comparison with price range
- **CCI (Commodity Channel Index)** - Cyclical trend identification

### Trend Indicators
- **ADX (Average Directional Index)** - Trend strength measurement
- **Moving Averages** - Simple, Exponential, Weighted
- **TRIX** - Triple exponential smoothing oscillator

### Volatility Indicators
- **Bollinger Bands** - Volatility and price deviation
- **ATR (Average True Range)** - Volatility measurement
- **Keltner Channels** - Volatility-based envelopes

### Volume Indicators
- **OBV (On-Balance Volume)** - Volume flow momentum
- **Money Flow Index** - Volume-weighted RSI
- **Volume-weighted Average Price** - Trading volume analysis

### Support & Resistance
- **Pivot Points** - Key price levels for reversals
- **Fibonacci Retracements** - Natural support/resistance levels
- **Dynamic Support/Resistance** - Adaptive level detection

### AI-Enhanced Analysis
- **LLM Advisor** - Natural language market interpretation
- **Deep Analyzer** - Claude AI comprehensive market context
- **Sentiment Analysis** - Real-time news and social sentiment
- **Divergence Detection** - Price/indicator divergences

## Configuration Deep Dive

The bot's behavior can be extensively customized through `config/config.py`:

### Trading Parameters
- **Tradable Coins:** Configure which coins to trade (default: BTC, SOL)
- **Initial Balances:** Set starting capital for simulation/live trading
- **Volume Limits:** Min/max position sizes per coin
- **Confidence Threshold:** Minimum confidence score to execute trades (0.0-1.0)

### Risk Management
- **Stop Loss:** Default 5% (configurable per strategy)
- **Take Profit:** Base 10% with dynamic adjustments
- **Trailing Stop:** 5% trailing from highest price
- **Max Drawdown:** 15% portfolio-level protection
- **Cooldown Period:** 300 seconds between trades (prevents overtrading)

### AI/LLM Configuration
- **LLM Enabled:** Toggle LLM advisor (requires API key)
- **LLM Final Authority:** Give LLM veto power over trades
- **Deep Analysis:** Enable comprehensive Claude AI analysis
- **ML Models:** Enable/disable ML price prediction
- **News Sentiment:** Toggle news analysis integration

### Exchange Configuration
- Only Kraken exchange is supported
- Configure Kraken API credentials in `.env`
- Kraken-specific pair mappings are configured in `config/config.py`

### Indicator Weights
Fine-tune how much each indicator contributes to trade decisions:
```python
'indicator_weights': {
    'macd': 0.4,
    'rsi': 0.2,
    'moving_avg': 0.2,
    'stochastic_oscillator': 0.1,
    'atr': 0.1,
    'btc_momentum': 0.2,
    'adx': 0.1,
    'obv': 0.1
}
```

## Testing

The project includes comprehensive test suites:

```bash
# Test Kraken connection
python diagnose_kraken.py

# Test LLM integration
python test_llm_advisor.py
python test_deep_analyzer.py
python test_ollama_connection.py

# Test Discord notifications
python test_discord_analysis.py
python test_all_discord_notifications.py

# Test ML models
python test_deep_analyzer_model.py

# Run unit tests
pytest
```

## Performance Monitoring

Monitor your bot's performance through:

1. **Web Dashboard** - `http://localhost:5000/dashboard`
   - Real-time price charts
   - Live trade execution log
   - Balance and P&L tracking
   - Indicator visualizations

2. **Log Files** - Comprehensive logging system
   - `simulate.log` - Simulation trades and decisions
   - `live_trade.log` - Live trading activity
   - `deep_analyzer.log` - AI analysis results
   - `llm_advisor.log` - LLM trading signals
   - `trade_log.json` - Structured trade history

3. **Trade Analytics**
   ```bash
   python scripts/analyze_trade_outcomes.py
   ```

## Troubleshooting Common Issues

### API Connection Errors
- Verify API keys in `.env` file
- Check exchange API status pages
- Ensure IP is whitelisted (if required by exchange)
- Verify API key permissions (trading, balance reading)

### LLM/AI Errors
- Confirm ANTHROPIC_API_KEY is valid
- Check API rate limits and billing
- Verify OpenRouter key as fallback
- Review `deep_analyzer.log` for specific errors

### WebSocket Connection Issues
- Check firewall settings (port 5000)
- Ensure eventlet is installed (`pip install eventlet`)
- Verify WebSocket support in browser (modern browsers)
- Review `websocket.log` for connection details

### ML Model Errors
- Ensure PyTorch is installed (`pip install torch`)
- For GPU: Verify CUDA installation
- Check model files exist in `models/` directory
- Review `ml_predictor.log` for issues

## Contribution

Contributions are welcome! Areas for improvement:
- Additional exchange integrations
- New technical indicators
- Enhanced ML models
- Improved risk management strategies
- UI/UX enhancements

Please fork the repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **IMPORTANT RISK DISCLOSURE** ⚠️

Trading cryptocurrencies carries substantial risk of loss and is not suitable for all investors. Key risks include:

- **Volatility:** Cryptocurrency prices can fluctuate dramatically
- **Capital Loss:** You may lose your entire investment
- **Technical Failures:** Software bugs, network issues, or API failures can result in losses
- **AI Limitations:** LLM and ML models are not infallible and can make incorrect predictions
- **Exchange Risk:** Exchange outages, hacks, or insolvency can affect your funds

This bot is provided **AS-IS** with **NO WARRANTIES** or guarantees of profitability. The developers are not responsible for any financial losses incurred through use of this software.

**Recommendations:**
- Start with simulation mode to understand the bot's behavior
- Use small amounts initially when transitioning to live trading
- Never invest more than you can afford to lose
- Regularly monitor bot performance and logs
- Keep API keys secure and use IP whitelisting when possible
- Maintain adequate risk management (stop losses, position sizing)
- Do your own research (DYOR) before making trading decisions

By using this software, you acknowledge these risks and accept full responsibility for any trading decisions and outcomes.

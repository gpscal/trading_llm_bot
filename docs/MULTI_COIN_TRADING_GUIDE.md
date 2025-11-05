# Multi-Coin Trading Guide

## Overview

The trading bot now supports trading multiple coins (SOL and BTC) with a single active trading coin at a time. The system maintains balances for all coins but executes trades only on the selected coin.

## Key Features

- **Multi-coin balance tracking**: Track USDT, SOL, and BTC balances simultaneously
- **Coin selection**: Choose which coin to trade (SOL or BTC) via CLI arguments
- **Dual indicators**: Both BTC and SOL indicators are calculated and used for trading decisions, regardless of which coin is being traded
- **LLM integration**: LLM advisor receives context for both coins and the selected trading coin
- **Per-coin risk management**: Stop-loss, take-profit, and trailing stops are tracked per coin
- **Portfolio-level metrics**: Total portfolio value, drawdown, and gains across all assets

## Architecture

### Configuration (`config/config.py`)

New configuration options:
```python
'tradable_coins': ['SOL', 'BTC']  # List of supported coins
'default_coin': 'SOL'              # Default trading coin
'initial_coin_balances': {
    'SOL': 10.0,
    'BTC': 0.01
}
'coin_volume_limits': {
    'SOL': {'min': 0.1, 'max': 10},
    'BTC': {'min': 0.0001, 'max': 0.25}
}
'coin_pairs': {
    'SOL': {
        'rest': 'SOLUSDT',
        'websocket': 'SOL/USD'
    },
    'BTC': {
        'rest': 'XXBTZUSD',
        'websocket': 'XBT/USD'
    }
}
```

### Balance Structure

The balance object now uses a hierarchical structure:

```python
balance = {
    'usdt': 1000.0,
    'selected_coin': 'SOL',
    'coins': {
        'SOL': {
            'amount': 10.0,
            'price': 150.0,
            'indicators': {...},
            'historical': [...],
            'position_entry_price': None,
            'trailing_high_price': None
        },
        'BTC': {
            'amount': 0.01,
            'price': 65000.0,
            'indicators': {...},
            'historical': [...],
            'position_entry_price': None,
            'trailing_high_price': None
        }
    },
    'initial_total_usd': 2150.0,
    'peak_total_usd': 2150.0,
    'last_trade_time': 0
}
```

### Coin Pair Manager

The `CoinPairManager` utility (`utils/coin_pair_manager.py`) provides:
- Pair name resolution (REST API vs WebSocket pairs)
- Volume limit retrieval per coin
- Initial balance configuration
- Validation of supported coins

## Usage

### Simulation Mode

Run simulation with coin selection:

```bash
# Trade SOL (default)
python simulate.py

# Trade BTC
python simulate.py --coin BTC

# Custom initial balances
python simulate.py --coin SOL --initial_balance_usdt 5000 --initial_balance_sol 20

# Trade BTC with custom BTC balance
python simulate.py --coin BTC --initial_balance_usdt 10000 --initial_balance_btc 0.1
```

### Live Trading Mode

Run live trading with coin selection:

```bash
# Trade SOL (default)
python live_trade.py

# Trade BTC
python live_trade.py --coin BTC
```

### Environment Variables

You can set defaults in `.env`:

```bash
DEFAULT_COIN=BTC
INITIAL_BALANCE_USDT=5000
INITIAL_BALANCE_SOL=10
INITIAL_BALANCE_BTC=0.05
MIN_VOLUME_SOL=0.1
MAX_VOLUME_SOL=10
MIN_VOLUME_BTC=0.0001
MAX_VOLUME_BTC=0.25
```

## Trading Logic

### Indicator Calculation

- **Both BTC and SOL indicators are always calculated** regardless of which coin is being traded
- Indicators include: MACD, RSI, ADX, OBV, momentum, moving averages, Bollinger Bands, ATR, stochastic oscillator
- Cross-coin correlation is calculated to understand market relationships

### Trade Decision

The selected coin (primary) uses:
1. **Primary indicators**: Indicators of the coin being traded
2. **Secondary indicators**: Indicators of the other coin (for market context)
3. **Dual-indicator conditions**: Both coins' indicators must meet thresholds for confidence boost
4. **LLM advisor**: Receives both coins' data and the selected trading coin
5. **ML predictor**: Can use both coins' historical data

### Risk Management

Per-coin risk controls:
- Stop-loss: Triggers when price drops below entry price by configured percentage
- Take-profit: Triggers when price rises above entry price by configured percentage
- Trailing stop: Follows price up and triggers on pullback

Portfolio-level controls:
- Max drawdown: Liquidates position if total portfolio drops by configured percentage from peak

## LLM Integration

The LLM advisor receives:
- Selected trading coin
- Current prices for both BTC and SOL
- Indicators for both coins
- Current balances (USDT and coin amounts)
- Historical data for both coins (if available)

The LLM can:
- Approve or veto trades based on multi-coin market analysis
- Consider correlation between BTC and SOL
- Factor in overall market sentiment from both assets

## Logging and Analytics

### Trade Logs

Trade log entries now include:
```json
{
    "timestamp": "2025-11-05 10:30:00",
    "coin": "SOL",
    "action": "buy",
    "volume": 5.5,
    "price": 150.25,
    "balance_usdt": 178.63,
    "balance_coin": 15.5,
    "confidence": 0.75,
    "rsi_primary": 35.2,
    "rsi_secondary": 42.8,
    "macd_primary": -2.5,
    "macd_secondary": -50.3
}
```

### Dashboard Updates

The web dashboard will show:
- Currently selected trading coin
- Balances for all coins
- Price charts for primary and secondary coins
- Indicators for both BTC and SOL
- Portfolio-level metrics (total value, gain, drawdown)

## Migration from Single-Coin

### Backward Compatibility

The system maintains backward compatibility:
- Old `balance['sol']` and `balance['sol_price']` keys still exist
- Legacy functions continue to work
- Existing logs and state are preserved

### Upgrading Existing Installations

1. Update configuration with new coin settings
2. Set `default_coin` in config or environment
3. Run simulation or live trading with `--coin` argument
4. Monitor logs for any migration issues

## Future Enhancements

Potential future additions:
- Concurrent multi-coin trading (trade both SOL and BTC simultaneously)
- More coins (ETH, ADA, etc.)
- Dynamic coin switching based on market conditions
- Cross-coin arbitrage strategies
- Portfolio rebalancing

## Troubleshooting

### Common Issues

**Issue**: "Unsupported coin" error
- **Solution**: Use only 'SOL' or 'BTC' (case-insensitive)

**Issue**: Indicators not calculating
- **Solution**: Ensure both BTC and SOL historical data is fetched successfully

**Issue**: Volume limits too restrictive
- **Solution**: Adjust `coin_volume_limits` in config or environment variables

**Issue**: Prices not updating
- **Solution**: Check websocket connection for both BTC and SOL pairs

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python simulate.py --coin BTC
```

Check logs:
- `simulate.log`: Simulation-specific logs
- `trade_logic.log`: Trade decision logs
- `data_fetchers.log`: Price and indicator fetching logs
- `orchestrator.log`: Trading loop logs

## API Reference

### Key Functions

- `get_coin_pair_manager()`: Get singleton coin pair manager
- `fetch_initial_price(coin)`: Fetch initial price for a coin
- `calculate_volume(price, balance, config, coin)`: Calculate trade volume for coin
- `handle_trade_with_fees(..., selected_coin)`: Execute trade with coin selection
- `run_trading_loop(..., selected_coin)`: Run trading loop for selected coin

### Configuration Keys

- `tradable_coins`: List of supported coins
- `default_coin`: Default trading coin
- `initial_coin_balances`: Initial balances per coin
- `coin_volume_limits`: Volume limits per coin
- `coin_pairs`: API pair mappings per coin

## Examples

### Example 1: SOL Day Trading Simulation

```bash
python simulate.py \
  --coin SOL \
  --initial_balance_usdt 10000 \
  --initial_balance_sol 0
```

### Example 2: BTC Swing Trading Simulation

```bash
python simulate.py \
  --coin BTC \
  --initial_balance_usdt 50000 \
  --initial_balance_btc 0.5
```

### Example 3: Live BTC Trading

```bash
python live_trade.py --coin BTC
```

## Support

For issues or questions:
1. Check logs in project root
2. Review configuration in `config/config.py`
3. Consult integration plan in `integrate_btc_trading.txt`
4. Check shared state in `utils/shared_state.py`

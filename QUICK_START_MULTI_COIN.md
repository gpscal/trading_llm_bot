# Quick Start: Multi-Coin Trading

## ?? Quick Commands

### Simulation Mode

```bash
# Default: Trade SOL
python simulate.py

# Trade BTC
python simulate.py --coin BTC

# Custom balances
python simulate.py --coin SOL --initial_balance_usdt 5000 --initial_balance_sol 20
python simulate.py --coin BTC --initial_balance_usdt 10000 --initial_balance_btc 0.1
```

### Live Trading Mode

```bash
# Default: Trade SOL
python live_trade.py

# Trade BTC
python live_trade.py --coin BTC
```

## ?? What's New

- ? **Multi-coin support**: Trade SOL or BTC (one at a time)
- ? **Dual indicators**: Both BTC and SOL indicators used for all trades
- ? **LLM integration**: AI advisor sees full market context
- ? **Per-coin risk management**: Stop-loss, take-profit per coin
- ? **Portfolio tracking**: Total value across all assets

## ?? Key Features

| Feature | Description |
|---------|-------------|
| **Coin Selection** | Choose SOL or BTC via `--coin` argument |
| **Dual Indicators** | Both coins analyzed regardless of which is traded |
| **Smart Volume** | Coin-specific min/max volume limits |
| **LLM Advisor** | Receives context for both coins |
| **Risk Controls** | Per-coin stop-loss, take-profit, trailing stops |
| **Portfolio Metrics** | Total USD value, gain/loss across all coins |

## ?? Configuration

### Environment Variables (.env)

```bash
# Set default trading coin
DEFAULT_COIN=SOL

# Initial balances
INITIAL_BALANCE_USDT=1000
INITIAL_BALANCE_SOL=10
INITIAL_BALANCE_BTC=0.01

# Volume limits
MIN_VOLUME_SOL=0.1
MAX_VOLUME_SOL=10
MIN_VOLUME_BTC=0.0001
MAX_VOLUME_BTC=0.25
```

### Supported Coins

- **SOL** (Solana) - Default
- **BTC** (Bitcoin)

More coins coming soon: ETH, MATIC, ADA

## ?? CLI Arguments

### simulate.py

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--coin` | str | SOL | Coin to trade (SOL or BTC) |
| `--initial_balance_usdt` | float | 1000 | Initial USDT balance |
| `--initial_balance_sol` | float | 10 | Initial SOL balance |
| `--initial_balance_btc` | float | 0.01 | Initial BTC balance |

### live_trade.py

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--coin` | str | SOL | Coin to trade (SOL or BTC) |

## ?? Important Files

- `config/config.py` - Multi-coin configuration
- `utils/coin_pair_manager.py` - Coin pair management utility
- `docs/MULTI_COIN_TRADING_GUIDE.md` - Comprehensive guide
- `docs/BTC_INTEGRATION_SUMMARY.md` - Integration details

## ?? Troubleshooting

**Error: "Unsupported coin"**
- Use 'SOL' or 'BTC' (case-insensitive)

**Error: "Failed to fetch prices"**
- Check internet connection
- Verify Kraken API is accessible

**Error: "Volume too low/high"**
- Adjust `coin_volume_limits` in config.py
- Or set MIN_VOLUME_* / MAX_VOLUME_* environment variables

## ?? Example Output

```
Starting simulation with coin=BTC, initial balances: USDT=10000, SOL=0, BTC=0.1
Fetching initial prices for SOL and BTC...
Fetched initial BTC price 68500.50 from XXBTZUSD
Fetched initial SOL price 155.75 from SOLUSD

Trading: BTC
USDT Balance: $10000.00
SOL: 0.000000 @ $155.75 = $0.00
BTC: 0.10000000 @ $68500.50 = $6850.05
Total Portfolio Value: $16850.05
Total Gain: $0.00 (0.00%)
```

## ?? Learn More

- **Full Guide**: [docs/MULTI_COIN_TRADING_GUIDE.md](docs/MULTI_COIN_TRADING_GUIDE.md)
- **Integration Summary**: [docs/BTC_INTEGRATION_SUMMARY.md](docs/BTC_INTEGRATION_SUMMARY.md)
- **Original Plan**: [integrate_btc_trading.txt](integrate_btc_trading.txt)

## ?? Tips

1. **Start with simulation**: Test with `simulate.py` before live trading
2. **Use small amounts**: Start with minimal balances to test
3. **Monitor logs**: Check `*.log` files for detailed information
4. **LLM advisor**: Enabled by default, provides AI-powered trading signals
5. **Dual indicators**: Both BTC and SOL analyzed for better market context

## ?? Status

- ? **Core Functionality**: Complete
- ? **Simulation Mode**: Working
- ? **Live Trading Mode**: Working
- ? **Web Dashboard**: Pending updates
- ? **Automated Tests**: Pending

## ?? Support

For issues or questions:
1. Check log files in project root
2. Review [MULTI_COIN_TRADING_GUIDE.md](docs/MULTI_COIN_TRADING_GUIDE.md)
3. Consult [BTC_INTEGRATION_SUMMARY.md](docs/BTC_INTEGRATION_SUMMARY.md)

---

**Ready to trade?** Start with: `python simulate.py --coin BTC`

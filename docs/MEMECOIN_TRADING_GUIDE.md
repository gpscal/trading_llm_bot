# Memecoin Trading Guide for SolBot

This guide explains how to configure SolBot to trade memecoins, including technical requirements, code changes, and risk considerations.

## Overview

Your current bot trades **SOL/USD** and uses **BTC/USD** as a market indicator on Kraken. To trade memecoins, you have several options:

1. **Trade memecoins listed on Kraken** (easiest - uses existing infrastructure)
2. **Integrate with Solana DEX (Jupiter/Raydium)** (more complex - for Solana-native memecoins)
3. **Integrate with other CEX exchanges** (Binance, Coinbase, etc.)

## Option 1: Kraken Memecoins (Recommended for Start)

### What Memecoins Does Kraken Support?

Kraken supports various memecoins. Common ones include:
- **DOGE** (Dogecoin) - DOGEUSD
- **SHIB** (Shiba Inu) - SHIBUSD  
- **PEPE** (Pepe) - PEPEUSD (if available)
- **FLOKI** - FLOKIUSD (if available)
- **BONK** - BONKUSD (if available)

**Check available pairs:**
```bash
curl https://api.kraken.com/0/public/AssetPairs
```

### Required Code Changes

#### 1. Update Trading Pairs Configuration

**File: `simulate.py` and `live_trade.py`**

Change the pairs dictionary to use a memecoin instead of SOL:

```python
# For Dogecoin example
pairs = {
    'btc': 'XXBTZUSD',      # Keep BTC as market indicator
    'memecoin': 'DOGEUSD'   # Replace 'sol' with 'memecoin'
}
```

**File: `utils/data_fetchers.py`**

Update the function to fetch memecoin price instead of SOL:

```python
async def fetch_initial_memecoin_price():
    """Fetch initial memecoin price from Kraken."""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.kraken.com/0/public/Ticker?pair=DOGEUSD") as response:
            data = await response.json()
            if 'result' in data and 'DOGEUSD' in data['result']:
                memecoin_price = float(data['result']['DOGEUSD']['c'][0])
                return memecoin_price
    return None
```

#### 2. Update Balance Structure

**File: `simulate.py`**

Change balance structure from 'sol' to your memecoin:

```python
balance = {
    'usdt': initial_balance_usdt,
    'memecoin': initial_balance_memecoin,  # Instead of 'sol'
    'memecoin_price': memecoin_price,      # Instead of 'sol_price'
    'btc_price': 0.0,
    'btc_momentum': 0.0,
    'confidence': 0.0,
    'initial_total_usd': 0.0,
    'last_trade_time': 0,
    'btc_indicators': {},
    'memecoin_indicators': {}  # Instead of 'sol_indicators'
}
```

#### 3. Update WebSocket Subscriptions

**File: `simulate.py`**

```python
asyncio.create_task(start_websocket(
    url=CONFIG['websocket_url'],
    pairs=['XBT/USD', 'DOGE/USD'],  # Update WebSocket pair
    on_data=handle_websocket_data,
    balance=balance
))
```

#### 4. Update Trade Logic

**File: `trade/trade_logic.py`**

The trade logic is already somewhat generic, but you'll need to update variable names:
- `balance_sol` ? `balance_memecoin`
- `sol_current_price` ? `memecoin_current_price`
- `sol_indicators` ? `memecoin_indicators`
- `initial_sol_price` ? `initial_memecoin_price`

#### 5. Update Config for Memecoin-Specific Parameters

**File: `config/config.py`**

Add memecoin-specific thresholds (memecoins are MUCH more volatile):

```python
CONFIG = {
    # ... existing config ...
    
    # Memecoin-specific risk management (much tighter than SOL)
    'stop_loss_pct': 10,              # 10% stop loss (memecoins move fast)
    'base_take_profit_pct': 20,       # 20% take profit (memecoins can pump hard)
    'trailing_stop_pct': 8,           # 8% trailing stop
    'max_drawdown_pct': 25,           # Higher max drawdown tolerance
    
    # Memecoin indicator thresholds (adjust for higher volatility)
    'macd_threshold': {
        'btc': -50,
        'memecoin': -0.1  # Much smaller threshold for memecoins
    },
    
    # Volume constraints for memecoins (often lower liquidity)
    'max_volume': 1000,               # Adjust based on memecoin liquidity
    'min_volume': 1,                   # Minimum trade size
    
    # Memecoin trading pair
    'trading_pair': 'DOGEUSD',        # Or your chosen memecoin
}
```

### Risk Management for Memecoins

**?? CRITICAL: Memecoins are EXTREMELY volatile and risky!**

1. **Tighter Stop Losses**: Use 8-12% stop losses (vs 5% for SOL)
2. **Faster Take Profits**: Set 15-25% take profit targets
3. **Lower Position Sizes**: Never risk more than 2-5% of portfolio per trade
4. **Shorter Hold Times**: Memecoins can dump fast - exit quickly on profits
5. **Liquidity Checks**: Ensure adequate volume before trading

### Testing Steps

1. **Test in Simulation First:**
   ```bash
   python simulate.py --initial_balance_usdt 100 --initial_balance_memecoin 0
   ```

2. **Monitor Performance:**
   - Check trade_log.json for trade history
   - Watch for slippage issues
   - Verify stop losses trigger correctly

3. **Start with Small Amounts:**
   - Use minimal capital in live trading
   - Test for at least 1 week in simulation

---

## Option 2: Solana DEX Integration (For Native Memecoins)

For trading Solana-native memecoins (like BONK, POPCAT, WIF, etc.), you'd need to integrate with:

- **Jupiter Aggregator** (recommended)
- **Raydium**
- **Orca**

### Required Changes

This requires significant code changes:

1. **New DEX API Client** (`api/jupiter.py` or `api/raydium.py`)
2. **Solana Wallet Integration** (using `solana-py` or `solders`)
3. **Token Address Mapping** (each memecoin has a token mint address)
4. **Slippage Handling** (DEX trades have variable slippage)
5. **Gas/Transaction Fees** (SOL for transaction fees)

### Example Structure

```python
# api/jupiter.py
async def swap_tokens(
    input_mint: str,      # Token address (e.g., "So11111111111111111111111111111111111111112" for SOL)
    output_mint: str,     # Memecoin token address
    amount: float,
    slippage_bps: int = 100  # 1% slippage
):
    # Jupiter API integration
    pass
```

**This is a much more complex implementation and requires:**
- Solana wallet setup
- SOL for transaction fees
- Understanding of token addresses and decimals
- Slippage and price impact calculations

---

## Option 3: Multi-Exchange Support

Integrate with multiple exchanges to access more memecoins:

- **Binance** (largest selection of memecoins)
- **Coinbase** (limited memecoins)
- **Bybit** (good memecoin selection)

This requires:
1. Multiple exchange API integrations
2. Exchange-specific pair naming
3. Unified trading interface

---

## Quick Start: Trading DOGE on Kraken

Here's the minimal changes needed to trade Dogecoin:

### Step 1: Update `simulate.py`

```python
# Line 69-72
pairs = {
    'btc': 'XXBTZUSD',
    'memecoin': 'DOGEUSD'  # Changed from 'sol': 'SOLUSDT'
}

# Line 40-50 - Update balance structure
balance = {
    'usdt': initial_balance_usdt,
    'doge': 0,  # Changed from 'sol'
    'doge_price': doge_price,  # Fetch DOGE price
    # ... rest stays same but replace 'sol' with 'doge'
}
```

### Step 2: Update `utils/data_fetchers.py`

Add function to fetch DOGE price:
```python
async def fetch_initial_doge_price():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.kraken.com/0/public/Ticker?pair=DOGEUSD") as response:
            data = await response.json()
            if 'result' in data and 'DOGEUSD' in data['result']:
                return float(data['result']['DOGEUSD']['c'][0])
    return None
```

### Step 3: Update WebSocket

```python
# Line 85 in simulate.py
pairs=['XBT/USD', 'DOGE/USD'],  # Changed from 'SOL/USD'
```

### Step 4: Update Config for Volatility

```python
# config/config.py
'stop_loss_pct': 10,        # Higher stop loss for volatility
'base_take_profit_pct': 20, # Higher take profit targets
```

---

## Recommendations

### For Beginners:
1. **Start with Kraken memecoins** (DOGE, SHIB) - uses existing code with minimal changes
2. **Test extensively in simulation** - memecoins are unpredictable
3. **Use small position sizes** - never risk more than you can afford to lose
4. **Monitor closely** - memecoins can move 50%+ in hours

### For Advanced Users:
1. **Consider DEX integration** for access to more memecoins
2. **Implement multi-exchange support** for better liquidity
3. **Add memecoin-specific indicators** (social sentiment, holder count, etc.)
4. **Use tighter risk controls** than main coins

---

## Risk Warnings

?? **MEMECOINS ARE EXTREMELY RISKY**

- Can lose 50-90% of value in hours
- Low liquidity can cause massive slippage
- Pump and dump schemes are common
- Regulatory uncertainty
- Technical failures more common
- Rug pulls and scams

**Only trade memecoins with money you can afford to lose completely!**

---

## Need Help?

If you want me to help implement memecoin trading for a specific coin, let me know:
1. Which memecoin you want to trade
2. Which exchange you prefer
3. Your risk tolerance level

I can help create the specific code changes needed!

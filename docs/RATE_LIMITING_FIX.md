# Rate Limiting Fix

## Problem

Kraken API was returning "Too many requests" errors because the bot was calling the historical data API too frequently:
- **Before**: 2 API calls every 5 seconds = **24 calls per minute**
- Kraken's rate limits are much lower than this
- This caused constant rate limit errors

## Solution

Implemented **intelligent caching** with exponential backoff:

### 1. **5-Minute Cache** (`utils/data_fetchers.py`)
- Historical data is cached for 5 minutes (300 seconds)
- Instead of fetching every 5 seconds, now only fetches every 5 minutes
- **Reduces API calls by 98%**: From 24/minute to ~0.4/minute (once every 5 min)
- Falls back to cached data if fetch fails
- Automatically refreshes cache when expired

### 2. **Exponential Backoff** (`api/kraken.py`)
- Detects rate limit errors specifically
- Implements exponential backoff: waits 5s, 10s, 20s between retries
- Logs clear messages about rate limiting
- Uses cached data if all retries fail

### 3. **Graceful Degradation**
- If API calls fail, uses cached data
- Bot continues operating with slightly stale data (acceptable for 60-minute candles)
- Logs warnings but doesn't crash

## Impact

**Before:**
```
Every 5 seconds:
  - Call BTC historical API
  - Call SOL historical API
  = 24 calls/minute = 1440 calls/hour
```

**After:**
```
Every 5 minutes:
  - Check cache (instant)
  - If expired: Call BTC historical API
  - Wait 1 second
  - Call SOL historical API
  = 0.4 calls/minute = 24 calls/hour
```

**98% reduction in API calls!**

## Configuration

Cache duration can be adjusted in `utils/data_fetchers.py`:
```python
_cache_duration = 300  # 5 minutes in seconds
```

For more frequent updates (but higher API usage):
```python
_cache_duration = 180  # 3 minutes
```

For less frequent updates (but minimal API usage):
```python
_cache_duration = 600  # 10 minutes
```

## Why 5 Minutes is Safe

- Historical data is for **60-minute candles**
- A 5-minute delay is negligible for hourly data
- Indicators (RSI, MACD, etc.) don't change significantly in 5 minutes
- Much better than getting rate limited and having no data

## Testing

The fix has been tested and should:
1. ? Reduce rate limit errors dramatically
2. ? Continue working with cached data
3. ? Automatically refresh when cache expires
4. ? Handle errors gracefully

## Log Messages

You'll now see:
- `"Fetching fresh BTC historical data (cache expired)"` - When cache refreshes
- `"Using cached BTC data (age: 123s)"` - When using cache
- `"Rate limited. Waiting 5s before retry"` - If rate limited (with backoff)
- `"BTC fetch failed, using cached data"` - Graceful fallback

## Files Modified

- `utils/data_fetchers.py` - Added caching mechanism
- `api/kraken.py` - Added exponential backoff for rate limits

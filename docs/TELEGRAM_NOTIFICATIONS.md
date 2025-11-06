# ?? Telegram Bot Notifications

Your trading bot can now send real-time notifications to Telegram when signals change!

## Features

? **Signal Change Alerts** - Get notified when LLM advisor changes signals (BUY ? SELL ? HOLD)  
? **LLM Advisor Feedback** - Brief summary of LLM reasoning for each signal  
? **Deep Analysis** - Comprehensive AI analysis summary (if enabled)  
? **Trade Execution Alerts** - Confirmation when trades are executed  
? **Error Notifications** - Get alerted about critical errors  

## Setup Instructions

### Step 1: Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to name your bot
4. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

**Option A: Using your bot**
1. Send any message to your new bot
2. Visit this URL in your browser (replace `<YOUR_BOT_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id": 123456789}` in the response
4. That number is your chat ID

**Option B: Using @userinfobot**
1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. Your ID will be displayed

### Step 3: Configure Environment Variables

Edit your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_API=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=your_chat_id_here
```

Replace:
- `TELEGRAM_API` with your bot token from Step 1
- `TELEGRAM_CHAT_ID` with your chat ID from Step 2

### Step 4: Test Your Configuration

Run the test script:

```bash
cd /home/cali/trading_llm_bot
python test_telegram_notifications.py
```

You should receive test messages in Telegram! ??

## Notification Types

### 1. Signal Change Alert

Triggered when the LLM advisor changes its signal (e.g., HOLD ? BUY).

**Contains:**
- Old signal ? New signal
- Current coin price
- Trading confidence score
- LLM advisor analysis (first 300 characters)
- Recommended stop loss / take profit levels
- Deep analysis summary (if available)

**Example:**
```
?? Signal Change Alert
??????????????????
Coin: BTC
Time: 2025-11-06 14:30:00
Price: $98,500.50

Signal Change:
?? HOLD ? ?? BUY
Confidence: 82.0%

?? LLM Advisor:
?? Signal: BUY
?? Confidence: HIGH (85.0%)
?? Analysis:
Strong bullish momentum detected. RSI shows oversold conditions recovering...
?? Stop Loss: $95,000.00
?? Take Profit: $102,000.00
??????????????????
```

### 2. Trade Execution Alert

Sent immediately when a trade is executed.

**Contains:**
- Buy/Sell action
- Amount traded
- Execution price
- Total value
- Updated balances

**Example:**
```
?? Trade Executed
??????????????????
Action: BUY BTC
Amount: 0.0150 BTC
Price: $98,500.50
Total: $1,477.51
Time: 2025-11-06 14:30:15

?? Balance:
USDT: $8,522.49
BTC: 0.015000
??????????????????
```

### 3. Error Alerts

Critical errors and warnings.

**Example:**
```
?? Trading Bot Error
??????????????????
Time: 2025-11-06 14:30:00
Context: trade_logic

LLM advisor connection timeout
??????????????????
```

## Configuration in Code

The Telegram notifier is automatically initialized from your `.env` file. It integrates seamlessly with:

- **Signal Tracker** (`utils/signal_tracker.py`) - Tracks signal changes
- **Trade Logic** (`trade/trade_logic.py`) - Sends notifications on signal changes and trades
- **Telegram Notifier** (`utils/telegram_notifier.py`) - Handles all Telegram API calls

### Signal Change Detection

The bot tracks signals per coin and only sends notifications when they actually change:

```python
from utils.signal_tracker import get_signal_tracker

tracker = get_signal_tracker()
changed, old_signal = tracker.check_signal_change('BTC', 'BUY')

if changed:
    # Send notification
    telegram.send_signal_change_alert(...)
```

### Disable Notifications

To disable Telegram notifications, simply remove or comment out the environment variables:

```bash
# TELEGRAM_API=...
# TELEGRAM_CHAT_ID=...
```

The bot will continue working normally without sending notifications.

## Troubleshooting

### Not Receiving Messages?

1. **Check bot token**: Make sure it's correct in `.env`
2. **Check chat ID**: Verify with @userinfobot
3. **Start conversation**: Send `/start` to your bot in Telegram
4. **Check logs**: 
   ```bash
   tail -f telegram_notifier.log
   ```
5. **Test manually**:
   ```bash
   python test_telegram_notifications.py
   ```

### Rate Limiting

Telegram has rate limits:
- **Individual chats**: 30 messages per second
- **Same message**: No more than 1 per minute to same user

The bot automatically handles this by:
- Only sending notifications when signals **actually change**
- Using signal tracker to prevent duplicate alerts
- Graceful error handling (logs warnings but doesn't crash)

### Privacy & Security

?? **Important**: Your bot token is like a password!
- Never commit `.env` to git (it's in `.gitignore`)
- Don't share your bot token publicly
- If compromised, revoke it via @BotFather and create a new one

### Group Chats

To use with a group chat:
1. Add your bot to the group
2. Make it an admin (or disable privacy mode via @BotFather)
3. Send a message in the group
4. Get the group's chat ID using the `/getUpdates` method
5. Group IDs are negative numbers (e.g., `-1001234567890`)

## Advanced Usage

### Custom Notifications

You can send custom notifications from anywhere in your code:

```python
from utils.telegram_notifier import get_telegram_notifier

telegram = get_telegram_notifier()

# Simple message
telegram.send_message("Custom alert message")

# With HTML formatting
message = "<b>Bold text</b>\n<i>Italic text</i>\n<code>Code block</code>"
telegram.send_message(message, parse_mode='HTML')
```

### Signal Tracker State

Signal state is persisted in `signal_state.json`:

```json
{
  "signals": {
    "BTC": "BUY",
    "SOL": "HOLD"
  },
  "last_updated": "2025-11-06T14:30:00"
}
```

Reset all signals:
```python
from utils.signal_tracker import get_signal_tracker
tracker = get_signal_tracker()
tracker.reset_all()
```

## Integration Points

The Telegram notifications are integrated at these key points:

1. **Signal Change Detection** (`trade/trade_logic.py:445-464`)
   - Checks for LLM signal changes
   - Sends notification with LLM + Deep Analysis feedback

2. **Trade Execution** (`trade/trade_logic.py:636-649`)
   - Sends confirmation after successful trades
   - Includes updated balances

3. **Error Handling** (can be added anywhere)
   - Use `telegram.send_error_alert()` for critical errors

## Files Overview

| File | Purpose |
|------|---------|
| `utils/telegram_notifier.py` | Telegram API integration |
| `utils/signal_tracker.py` | Track signal changes per coin |
| `test_telegram_notifications.py` | Test script |
| `signal_state.json` | Persisted signal state |
| `.env` | Configuration (bot token + chat ID) |

## Example Output

When your bot is running and signals change, you'll see:

**In Logs:**
```
[2025-11-06 14:30:00] Signal changed for BTC: HOLD ? BUY
[2025-11-06 14:30:00] Telegram message sent successfully
[2025-11-06 14:30:15] ? LLM Advisor APPROVES trade: BUY on BTC
[2025-11-06 14:30:15] Telegram message sent successfully
```

**In Telegram:**
- ?? Signal Change Alert (with full LLM analysis)
- ?? Trade Executed (with balances)

## Support

For issues or questions:
1. Check `telegram_notifier.log` for detailed logs
2. Run `test_telegram_notifications.py` to diagnose
3. Verify `.env` configuration
4. Check Telegram bot permissions

---

**Enjoy your real-time trading notifications!** ????

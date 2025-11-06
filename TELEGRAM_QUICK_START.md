# ?? Telegram Notifications - Quick Start

Get signal change notifications with LLM advisor feedback in just 3 steps!

## ?? Quick Setup (5 minutes)

### Step 1: Create Telegram Bot (2 min)

1. Open Telegram, search for **@BotFather**
2. Send: `/newbot`
3. Name your bot (e.g., "My Trading Bot")
4. Copy the **bot token** (looks like: `123456:ABCdef...`)

### Step 2: Get Your Chat ID (1 min)

**Easy way:**
1. Search for **@userinfobot** in Telegram
2. Send: `/start`
3. Copy your **ID number**

**OR** send a message to your bot and visit:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
Look for `"chat":{"id": YOUR_NUMBER}`

### Step 3: Update .env File (1 min)

Edit `/home/cali/trading_llm_bot/.env`:

```bash
TELEGRAM_API=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE
```

**Example:**
```bash
TELEGRAM_API=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## ? Test It!

```bash
cd /home/cali/trading_llm_bot
python test_telegram_notifications.py
```

You should receive **5 test messages** in Telegram:
1. ? Connection test
2. ?? Signal change alert (HOLD ? BUY)
3. ?? Trade execution alert
4. ?? Signal tracker test
5. ?? Error alert

## ?? What You'll Get

### Signal Change Notifications

When the LLM advisor changes signals (e.g., HOLD ? BUY), you'll receive:

```
?? Signal Change Alert
??????????????????
Coin: BTC
Price: $98,500.50

?? HOLD ? ?? BUY
Confidence: 82.0%

?? LLM Advisor:
Signal: BUY (HIGH confidence)
?? Analysis:
"Strong bullish momentum detected. RSI 
shows oversold conditions recovering, 
MACD crossed above signal line..."

?? Stop Loss: $95,000
?? Take Profit: $102,000
??????????????????
```

### Trade Execution Alerts

```
?? Trade Executed
??????????????????
Action: BUY BTC
Amount: 0.0150 BTC
Price: $98,500.50

?? Balance:
USDT: $8,522.49
BTC: 0.015000
??????????????????
```

## ?? Configuration

### Already configured in .env?

You're done! Just update these two lines:
```bash
TELEGRAM_API=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=your_chat_id_here  # ? Add your chat ID
```

### Disable notifications?

Comment out or remove:
```bash
# TELEGRAM_API=...
# TELEGRAM_CHAT_ID=...
```

## ?? Troubleshooting

**Not receiving messages?**

1. ? Check bot token in `.env`
2. ? Check chat ID in `.env`
3. ? Send `/start` to your bot in Telegram
4. ? Run test script: `python test_telegram_notifications.py`
5. ? Check logs: `tail -f telegram_notifier.log`

**Common issues:**

| Problem | Solution |
|---------|----------|
| "Unauthorized" error | Wrong bot token |
| "Chat not found" | Wrong chat ID or didn't start bot |
| No messages | Check bot privacy settings in @BotFather |

## ?? Full Documentation

See `docs/TELEGRAM_NOTIFICATIONS.md` for:
- Advanced features
- Group chat support
- Custom notifications
- API reference

## ?? You're All Set!

Your bot will now send you Telegram notifications when:
- ? Signals change (with LLM analysis)
- ? Trades are executed
- ? Critical errors occur

**Start your bot and wait for your first signal change!** ??

---

**Questions?** Check the logs:
```bash
tail -f telegram_notifier.log
tail -f trade_logic.log
```

# WhatsApp Message Templates

This directory contains all WhatsApp message templates for the trading bot.

## Template Files

Each `.json` file represents a WhatsApp message template that must be submitted to Twilio/WhatsApp for approval.

### Available Templates

1. **signal_change_alert.json** - Trading signal changes (BUY/SELL/HOLD)
2. **trade_execution.json** - Trade execution confirmations
3. **deep_market_analysis.json** - Comprehensive AI market analysis (every 2 hours)
4. **bot_status.json** - Bot connection and status updates
5. **error_alert.json** - Critical error notifications
6. **daily_summary.json** - Daily performance summary

## How to Use These Templates

### Step 1: Create in Twilio Console

1. Go to: https://console.twilio.com/us1/develop/sms/content-template-builder
2. Click **Create new Template**
3. Copy content from the `.json` file
4. Fill in the template details
5. Submit for WhatsApp approval

### Step 2: Get Content SID

After approval:
1. Go back to Content Template Builder
2. Find your approved template
3. Copy the **Content SID** (format: `HXxxxxxxxxx`)
4. Update the configuration in `whatsapp_templates/template_config.json`

### Step 3: Test Templates

Run the template test script:
```bash
python3 test_whatsapp_templates.py
```

## Template Guidelines

- **Variables**: Use `{{1}}`, `{{2}}`, etc. for dynamic content
- **Length**: Keep under 1024 characters
- **Category**: Use `ALERT_UPDATE` for trading notifications
- **Language**: English (can add more later)
- **Approval Time**: 24-48 hours typically

## Template Variables Reference

See each template file for specific variable definitions.

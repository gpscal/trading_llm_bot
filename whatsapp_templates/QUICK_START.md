# 🚀 WhatsApp Templates - Quick Start Guide

Get your trading bot's WhatsApp notifications working in 3 steps!

---

## ⚡ Step 1: Submit Templates (5 minutes)

### Go to Twilio Console

🔗 **URL:** https://console.twilio.com/us1/develop/sms/content-template-builder

### Create These Templates (in priority order):

#### 1️⃣ Deep Market Analysis (MOST IMPORTANT)

```
Template Name: deep_market_analysis
Category: ALERT_UPDATE
Language: English

Content: [Copy from deep_market_analysis.json]
```

**Why first?** This is your most valuable notification - comprehensive AI analysis every 2 hours!

#### 2️⃣ Signal Change Alert

```
Template Name: signal_change_alert
Category: ALERT_UPDATE
Language: English

Content: [Copy from signal_change_alert.json]
```

**Why second?** Real-time BUY/SELL/HOLD signals with AI reasoning.

#### 3️⃣ Trade Execution

```
Template Name: trade_execution
Category: ALERT_UPDATE
Language: English

Content: [Copy from trade_execution.json]
```

**Why third?** Get notified when trades execute with balance updates.

#### 4️⃣ Bot Status (Optional but Recommended)

```
Template Name: bot_status
Category: ALERT_UPDATE
Language: English

Content: [Copy from bot_status.json]
```

#### 5️⃣ Error Alert (Optional)

```
Template Name: error_alert
Category: ALERT_UPDATE
Language: English

Content: [Copy from error_alert.json]
```

#### 6️⃣ Daily Summary (Optional)

```
Template Name: daily_summary
Category: ALERT_UPDATE
Language: English

Content: [Copy from daily_summary.json]
```

### Submit Each Template

1. Click **"Submit for Approval"**
2. Wait for email confirmation (24-48 hours)
3. Come back when approved

---

## ⏰ Step 2: Wait for Approval (24-48 hours)

WhatsApp will review your templates. You'll receive emails when:
- ✅ Template is approved
- 📝 Changes are needed
- ❌ Template is rejected (rare)

### Meanwhile: Use Sandbox Mode for Testing

Want to test NOW while waiting? Use sandbox:

```bash
cd /home/cali/trading_llm_bot
python3 setup_whatsapp.py sandbox
```

Then text the join code to +14155238886 from your WhatsApp.

---

## ✅ Step 3: Configure Approved Templates (2 minutes)

### After Approval

1. Go back to: https://console.twilio.com/us1/develop/sms/content-template-builder
2. Find your approved template
3. Click on it
4. Copy the **Content SID** (starts with `HX...`)

### Update Configuration

Edit: `whatsapp_templates/template_config.json`

```json
{
  "templates": {
    "deep_market_analysis": {
      "content_sid": "HXyour_content_sid_here",  ← Paste here
      "status": "approved"                        ← Change to approved
    },
    ...
  }
}
```

Repeat for each approved template.

### Test Your Templates

```bash
python3 test_whatsapp_templates.py
```

Choose option 3 (Deep Market Analysis) to test the most comprehensive template!

---

## 🎯 Template Priority

If you only want to submit a few templates, prioritize this way:

### Must-Have (Submit These First)
1. ⭐⭐⭐ **deep_market_analysis** - Comprehensive AI insights every 2 hours
2. ⭐⭐⭐ **signal_change_alert** - Real-time BUY/SELL/HOLD signals
3. ⭐⭐ **trade_execution** - Trade confirmations

### Nice-to-Have
4. ⭐ **bot_status** - Health checks and startup confirmation
5. ⭐ **error_alert** - Error notifications

### Optional
6. **daily_summary** - End-of-day performance report

---

## 📁 Files in This Directory

```
whatsapp_templates/
├── README.md                          ← Overview
├── QUICK_START.md                     ← This file
├── VISUAL_TEMPLATE_EXAMPLES.md        ← See what messages look like
├── template_submission_guide.txt      ← Detailed submission guide
├── template_config.json               ← Configuration (update after approval)
│
├── deep_market_analysis.json          ← Template definition ⭐⭐⭐
├── signal_change_alert.json           ← Template definition ⭐⭐⭐
├── trade_execution.json               ← Template definition ⭐⭐
├── bot_status.json                    ← Template definition ⭐
├── error_alert.json                   ← Template definition ⭐
└── daily_summary.json                 ← Template definition
```

---

## 🎓 Detailed Guides

### Want to see what the messages will look like?
→ Read: `VISUAL_TEMPLATE_EXAMPLES.md`

### Need step-by-step submission instructions?
→ Read: `template_submission_guide.txt`

### Want to understand the configuration?
→ Read: `README.md`

---

## 🆘 Troubleshooting

### ❌ Template Rejected - "Too Long"
**Solution:** The template exceeds 1024 characters. Shorten the AI reasoning sections.

### ❌ Template Rejected - "Invalid Variables"
**Solution:** Variables must be {{1}}, {{2}}, {{3}} in sequential order. Cannot skip numbers.

### ⏳ Template Stuck in "Pending" for >48 hours
**Solution:** Contact Twilio support at support@twilio.com

### 🚫 Error 63016 - Outside Allowed Window
**Solution:** You're using a production number without approved templates. Either:
- Wait for template approval, or
- Switch to sandbox mode temporarily

---

## 💡 Pro Tips

1. **Submit all 6 templates at once** - They'll all be reviewed together
2. **Start with sandbox mode** - Test while waiting for approval
3. **Check your email** - WhatsApp sends approval notifications
4. **Test immediately** - Run `python3 test_whatsapp_templates.py` after approval
5. **Monitor logs** - `tail -f whatsapp_notifier.log` to see what's happening

---

## 🎉 What You'll Get

Once approved, you'll receive:

- 📊 **Comprehensive AI market analysis** every 2 hours
- 🚨 **Real-time trading signals** with AI reasoning
- 💰 **Trade execution confirmations** with balances
- 🤖 **Bot health status** updates
- ⚠️ **Error alerts** when issues occur
- 📈 **Daily performance summaries**

All professionally formatted with emojis, structure, and clarity!

---

## 🚀 Ready to Start?

1. Open: https://console.twilio.com/us1/develop/sms/content-template-builder
2. Click: "Create new Template"
3. Start with: `deep_market_analysis.json`
4. Copy the template content
5. Submit for approval
6. Repeat for other templates

**Estimated time:** 15 minutes to submit all 6 templates

**Approval time:** 24-48 hours

**Worth it?** Absolutely! Professional trading notifications! 🎯

---

Need help? Check the other guides in this directory or run:

```bash
python3 setup_whatsapp.py
```

Good luck! 🍀

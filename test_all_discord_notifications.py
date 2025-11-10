#!/usr/bin/env python3
"""
Test ALL Discord Notifications
Tests all 5 notification types: Signal Change, Trade Execution, Bot Status, Error Alert, Daily Summary
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from utils.discord_notifier import get_discord_notifier

load_dotenv()


async def test_all_notifications():
    print("\n" + "="*70)
    print("  Testing ALL Discord Notifications")
    print("  (SO much easier than WhatsApp!)")
    print("="*70 + "\n")
    
    # Initialize Discord
    print("📡 Connecting to Discord...")
    notifier = await get_discord_notifier()
    
    if not notifier.enabled:
        print("❌ Discord notifier not enabled!")
        sys.exit(1)
    
    print("✅ Connected to Discord!")
    print()
    
    results = {}
    
    # Test 1: Signal Change Alert
    print("1️⃣ Testing Signal Change Alert...")
    try:
        result = await notifier.send_signal_change_alert(
            coin='BTC',
            old_signal='HOLD',
            new_signal='BUY',
            price=75420.00,
            confidence=0.87,
            strategy='Momentum Breakout',
            llm_signal={
                'signal': 'BUY',
                'confidence': 'HIGH',
                'confidence_score': 0.90,
                'reasoning': 'Strong bullish momentum with RSI recovery from oversold conditions. Volume surge confirms buyer interest at support level.',
                'stop_loss': 73200.00,
                'take_profit': 78500.00
            }
        )
        results['signal_change'] = result
        print(f"   {'✅ SUCCESS' if result else '❌ FAILED'}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['signal_change'] = False
    
    await asyncio.sleep(2)
    
    # Test 2: Trade Execution Alert
    print("\n2️⃣ Testing Trade Execution Alert...")
    try:
        result = await notifier.send_trade_execution_alert(
            coin='BTC',
            action='BUY',
            amount=0.0125,
            price=75420.00,
            total_value=942.75,
            balance_usdt=57.25,
            balance_coin=0.0125,
            position_status="Holding BTC ($942.75)",
            trade_summary="Successfully entered position at current support level. Stop loss at $73,200. Target profit at $78,500."
        )
        results['trade_execution'] = result
        print(f"   {'✅ SUCCESS' if result else '❌ FAILED'}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['trade_execution'] = False
    
    await asyncio.sleep(2)
    
    # Test 3: Bot Status
    print("\n3️⃣ Testing Bot Status Alert...")
    try:
        result = await notifier.send_bot_status(
            status="ONLINE",
            message="Trading bot is connected and actively monitoring the market.",
            trading_engine="Active",
            market_data="Connected (Kraken)",
            ai_analysis="Running (Claude 4.5)",
            risk_management="Enabled",
            markets="BTC/USD, SOL/USD",
            ai_models="LLM Advisor + Deep Analyzer",
            update_interval="5 seconds",
            deep_analysis_interval="Every 2 hours",
            additional_info="You will receive real-time notifications for all trading signals and executed trades."
        )
        results['bot_status'] = result
        print(f"   {'✅ SUCCESS' if result else '❌ FAILED'}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['bot_status'] = False
    
    await asyncio.sleep(2)
    
    # Test 4: Error Alert
    print("\n4️⃣ Testing Error Alert...")
    try:
        result = await notifier.send_error_alert(
            error_type="API CONNECTION WARNING",
            component="Kraken WebSocket",
            severity="MEDIUM",
            error_description="WebSocket connection lost. Attempting automatic reconnection.",
            impact="Market data updates paused temporarily. No trades will be executed until connection is restored.",
            recommended_action="No action required. Bot is attempting automatic recovery. You will be notified when connection is restored.",
            trading_status="Paused",
            monitoring_status="Reconnecting",
            notification_status="Active",
            additional_context="Reconnection attempt 1/3. If issue persists, check your API credentials and network connection."
        )
        results['error_alert'] = result
        print(f"   {'✅ SUCCESS' if result else '❌ FAILED'}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['error_alert'] = False
    
    await asyncio.sleep(2)
    
    # Test 5: Daily Summary
    print("\n5️⃣ Testing Daily Summary...")
    try:
        result = await notifier.send_daily_summary(
            date="November 10, 2025",
            starting_balance=1000.00,
            ending_balance=1042.50,
            pnl=42.50,
            pnl_percent=4.25,
            total_trades=12,
            winning_trades=8,
            losing_trades=3,
            breakeven_trades=1,
            win_rate=0.667,
            avg_trade=3.54,
            best_trades=(
                "1. BTC BUY: +$18.50 (2.1%)\n"
                "2. SOL SELL: +$12.30 (5.8%)\n"
                "3. BTC SELL: +$8.40 (1.1%)"
            ),
            total_signals=47,
            signal_accuracy=0.723,
            ml_confidence_avg=0.785,
            current_positions="💵 100% USDT ($1,042.50)\nNo open positions",
            ai_insights="Strong day with consistent wins. BTC showed bullish momentum with successful breakout trades. Risk management performed well with minimal drawdown.",
            next_summary="Tomorrow at 23:59"
        )
        results['daily_summary'] = result
        print(f"   {'✅ SUCCESS' if result else '❌ FAILED'}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results['daily_summary'] = False
    
    # Summary
    print("\n" + "="*70)
    print("  Test Results Summary")
    print("="*70 + "\n")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name.replace('_', ' ').title():<30} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*70)
        print("  🎉 ALL TESTS PASSED!")
        print("="*70)
        print()
        print("✅ Check your Discord #trading_bot channel for 5 beautiful messages:")
        print()
        print("  1. 🚨 Signal Change Alert (HOLD → BUY)")
        print("  2. 🟢 Trade Executed (BUY 0.0125 BTC)")
        print("  3. ✅ Trading Bot ONLINE")
        print("  4. ⚠️  API CONNECTION WARNING")
        print("  5. 📊 Daily Trading Summary")
        print()
        print("💚 Discord is SO much easier than WhatsApp!")
        print("   No templates, no approval, no 3-day wait!")
        print()
    else:
        print("\n⚠️  Some tests failed. Check discord_notifier.log for details")
    
    print("="*70 + "\n")
    
    # Clean shutdown
    await notifier.close()
    
    return passed == total


if __name__ == '__main__':
    try:
        success = asyncio.run(test_all_notifications())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted\n")
        sys.exit(130)

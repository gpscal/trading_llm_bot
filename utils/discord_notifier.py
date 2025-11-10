"""
Discord Notification System
Sends trading signal alerts and deep market analysis to Discord
Much simpler than WhatsApp! 🎉
"""
import os
import discord
from discord.ext import commands
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
from utils.logger import setup_logger

logger = setup_logger('discord_notifier', 'discord_notifier.log')


class TradingDiscordBot:
    """Sends trading notifications to Discord"""
    
    def __init__(
        self, 
        token: Optional[str] = None,
        channel_id: Optional[str] = None
    ):
        """
        Initialize Discord notifier
        
        Args:
            token: Discord bot token
            channel_id: Discord channel ID
        """
        self.token = token or os.getenv('DISCORD_BOT_TOKEN')
        self.channel_id = channel_id or os.getenv('DISCORD_CHANNEL_ID')
        
        self.enabled = bool(self.token and self.channel_id)
        
        if not self.enabled:
            logger.warning(
                "Discord notifier disabled - missing credentials: "
                "DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID"
            )
            return
        
        try:
            self.channel_id = int(self.channel_id)
        except ValueError:
            logger.error(f"Invalid DISCORD_CHANNEL_ID: {self.channel_id}")
            self.enabled = False
            return
        
        # Setup bot with intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix='!trade', intents=intents)
        self.setup_events()
        self.is_ready = False
        
        logger.info(f"Discord notifier initialized (channel: {self.channel_id})")
    
    def setup_events(self):
        """Setup bot events"""
        
        @self.bot.event
        async def on_ready():
            self.is_ready = True
            logger.info(f'Discord Bot logged in as {self.bot.user.name} ({self.bot.user.id})')
            logger.info(f'Connected to {len(self.bot.guilds)} server(s)')
            
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                logger.info(f'Target channel: #{channel.name} in {channel.guild.name}')
            else:
                logger.warning(f'Could not find channel with ID {self.channel_id}')
    
    async def send_message(self, content: str) -> bool:
        """
        Send a message to Discord channel
        
        Args:
            content: Message content
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.debug("Discord disabled, skipping message")
            return False
        
        try:
            channel = self.bot.get_channel(self.channel_id)
            
            if not channel:
                logger.error(f"Could not find channel with ID {self.channel_id}")
                return False
            
            # Discord has 2000 character limit
            if len(content) > 2000:
                chunks = self._split_message(content)
                for chunk in chunks:
                    await channel.send(chunk)
                    await asyncio.sleep(1)
            else:
                await channel.send(content)
            
            logger.info(f"Message sent to #{channel.name}")
            return True
            
        except discord.errors.Forbidden:
            logger.error("Bot doesn't have permission to send messages")
            return False
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def _split_message(self, content: str, max_length: int = 2000) -> list:
        """Split long messages into chunks"""
        chunks = []
        current_chunk = ""
        
        for line in content.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def send_embed(
        self, 
        title: str, 
        description: str,
        fields: list = None,
        color: int = 0x00ff00
    ) -> bool:
        """
        Send formatted embed message
        
        Args:
            title: Embed title
            description: Embed description  
            fields: List of dicts with 'name', 'value', 'inline' keys
            color: Embed color (hex)
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            channel = self.bot.get_channel(self.channel_id)
            
            if not channel:
                logger.error(f"Could not find channel {self.channel_id}")
                return False
            
            embed = discord.Embed(
                title=title[:256],
                description=description[:4096],
                color=color,
                timestamp=datetime.utcnow()
            )
            
            if fields:
                for field in fields[:25]:
                    embed.add_field(
                        name=field.get('name', 'Field')[:256],
                        value=field.get('value', 'No value')[:1024],
                        inline=field.get('inline', False)
                    )
            
            await channel.send(embed=embed)
            logger.info(f"Embed sent to #{channel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send embed: {e}")
            return False
    
    async def send_deep_analysis_report(
        self,
        coin: str,
        price: float,
        analysis: Dict[str, Any]
    ) -> bool:
        """
        Send deep market analysis to Discord
        
        Args:
            coin: Trading coin (e.g., 'BTC')
            price: Current price
            analysis: Analysis data dictionary
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Extract analysis data
            trend = analysis.get('trend', 'NEUTRAL')
            action = analysis.get('recommended_action', 'HOLD')
            confidence = analysis.get('confidence', 0.0)
            risk_level = analysis.get('risk_level', 'MEDIUM')
            reasoning = analysis.get('reasoning', 'No reasoning provided')
            
            # Emoji mappings
            action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}
            trend_emoji = {'BULLISH': '📈', 'BEARISH': '📉', 'NEUTRAL': '➡️'}
            
            # Color mapping
            color_map = {'BUY': 0x00ff00, 'SELL': 0xff0000, 'HOLD': 0xffff00}
            
            # Build embed
            title = f"📊 Deep Market Analysis - {coin}/USD"
            description = f"**${price:,.2f}**\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            fields = []
            
            # Recommendation
            fields.append({
                'name': '🎯 AI Recommendation',
                'value': (
                    f"{action_emoji.get(action, '⚪')} **{action}**\n"
                    f"Confidence: {confidence:.0%}\n"
                    f"{trend_emoji.get(trend, '⚪')} Trend: **{trend}**\n"
                    f"Risk Level: **{risk_level}**"
                ),
                'inline': False
            })
            
            # Technical Indicators
            key_indicators = analysis.get('key_indicators', {})
            if key_indicators:
                rsi = key_indicators.get('rsi', 50)
                adx = key_indicators.get('adx', 20)
                volatility = key_indicators.get('volatility_ratio', 0.015)
                
                rsi_status = "Oversold" if rsi < 30 else ("Overbought" if rsi > 70 else "Neutral")
                adx_status = "Strong" if adx > 25 else "Weak"
                vol_status = "High" if volatility > 0.02 else ("Low" if volatility < 0.01 else "Moderate")
                
                fields.append({
                    'name': '📈 Technical Indicators',
                    'value': (
                        f"RSI: {rsi:.1f} ({rsi_status})\n"
                        f"ADX: {adx:.1f} ({adx_status} trend)\n"
                        f"Volatility: {vol_status}"
                    ),
                    'inline': True
                })
            
            # Price Levels
            support = analysis.get('support_levels', [])
            resistance = analysis.get('resistance_levels', [])
            if support or resistance:
                levels_text = ""
                if support and len(support) > 0:
                    levels_text += f"🟢 Support: ${support[0]:,.2f}\n"
                if resistance and len(resistance) > 0:
                    levels_text += f"🔴 Resistance: ${resistance[0]:,.2f}\n"
                
                stop_loss = analysis.get('stop_loss_suggestion')
                take_profit = analysis.get('take_profit_suggestion')
                if stop_loss:
                    levels_text += f"🛑 Stop Loss: ${stop_loss:,.2f}\n"
                if take_profit:
                    levels_text += f"🎯 Take Profit: ${take_profit:,.2f}"
                
                fields.append({
                    'name': '🎯 Key Levels',
                    'value': levels_text,
                    'inline': True
                })
            
            # AI Analysis
            fields.append({
                'name': '🤖 AI Deep Analysis',
                'value': reasoning[:1024],
                'inline': False
            })
            
            # Market Sentiment
            sentiment_score = analysis.get('sentiment_score')
            if sentiment_score:
                sentiment_value = int(sentiment_score * 100)
                fg_text = (
                    "Extreme Fear" if sentiment_value < 25 else
                    "Fear" if sentiment_value < 45 else
                    "Neutral" if sentiment_value < 55 else
                    "Greed" if sentiment_value < 75 else
                    "Extreme Greed"
                )
                
                macro_trend = analysis.get('macro_trend', '')
                
                fields.append({
                    'name': '🌍 Market Sentiment',
                    'value': (
                        f"Fear & Greed: {sentiment_value}/100 ({fg_text})\n"
                        f"{macro_trend[:200]}"
                    ),
                    'inline': False
                })
            
            # News Sentiment
            news_sentiment = analysis.get('news_sentiment', {})
            if news_sentiment:
                news_label = news_sentiment.get('label', 'NEUTRAL')
                article_count = news_sentiment.get('article_count', 0)
                news_emoji = {'BULLISH': '📰🟢', 'BEARISH': '📰🔴', 'NEUTRAL': '📰⚪'}
                
                headlines = news_sentiment.get('top_headlines', [])
                headlines_text = f"{news_emoji.get(news_label, '📰⚪')} **{news_label}**\n"
                headlines_text += f"From {article_count} articles\n\n"
                
                if headlines:
                    headlines_text += "Recent Headlines:\n"
                    for headline in headlines[:3]:
                        title = headline.get('title', '')[:80]
                        headlines_text += f"• {title}\n"
                
                fields.append({
                    'name': '📰 News Analysis',
                    'value': headlines_text[:1024],
                    'inline': False
                })
            
            # Patterns and Warnings
            patterns = analysis.get('key_patterns', [])
            warnings = analysis.get('warnings', [])
            if patterns or warnings:
                patterns_text = ""
                for pattern in patterns[:3]:
                    patterns_text += f"• {pattern}\n"
                for warning in warnings[:2]:
                    patterns_text += f"⚠️ {warning}\n"
                
                fields.append({
                    'name': '⚠️ Key Patterns & Warnings',
                    'value': patterns_text[:1024],
                    'inline': False
                })
            
            # Footer
            ai_model = analysis.get('ai_model_used', 'AI Trading Bot')
            fields.append({
                'name': 'ℹ️ Info',
                'value': f"Analyzed by {ai_model}\nNext analysis in ~2 hours",
                'inline': False
            })
            
            # Send embed
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=color_map.get(action, 0xffff00)
            )
            
        except Exception as e:
            logger.error(f"Failed to send deep analysis: {e}")
            return False
    
    async def send_signal_change_alert(
        self,
        coin: str,
        old_signal: str,
        new_signal: str,
        price: float,
        confidence: float,
        strategy: str = "AI Strategy",
        llm_signal: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send signal change alert to Discord
        
        Args:
            coin: Trading coin
            old_signal: Previous signal (BUY/SELL/HOLD)
            new_signal: New signal (BUY/SELL/HOLD)
            price: Current price
            confidence: Signal confidence (0-1)
            strategy: Strategy name
            llm_signal: Optional LLM advisor data
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Emoji mappings
            signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}
            
            # Color mapping
            color_map = {'BUY': 0x00ff00, 'SELL': 0xff0000, 'HOLD': 0xffff00}
            
            title = f"🚨 Signal Change Alert - {coin}"
            description = (
                f"**${price:,.2f}**\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            fields = []
            
            # Signal change
            fields.append({
                'name': '📊 Signal Update',
                'value': (
                    f"{signal_emoji.get(old_signal, '⚪')} {old_signal} → "
                    f"{signal_emoji.get(new_signal, '⚪')} **{new_signal}**\n"
                    f"Confidence: {confidence:.0%}\n"
                    f"Strategy: {strategy}"
                ),
                'inline': False
            })
            
            # LLM Advisor analysis
            if llm_signal:
                llm_signal_str = llm_signal.get('signal', 'HOLD')
                llm_confidence = llm_signal.get('confidence', 'UNKNOWN')
                llm_confidence_score = llm_signal.get('confidence_score', 0.0)
                reasoning = llm_signal.get('reasoning', 'No reasoning provided')
                
                fields.append({
                    'name': '🤖 AI Advisor Analysis',
                    'value': (
                        f"{signal_emoji.get(llm_signal_str, '⚪')} Signal: **{llm_signal_str}**\n"
                        f"Confidence: {llm_confidence} ({llm_confidence_score:.0%})\n"
                        f"Reasoning: {reasoning[:200]}"
                    ),
                    'inline': False
                })
                
                # Risk management
                stop_loss = llm_signal.get('stop_loss')
                take_profit = llm_signal.get('take_profit')
                if stop_loss or take_profit:
                    risk_text = ""
                    if stop_loss:
                        risk_text += f"🛑 Stop Loss: ${stop_loss:,.2f}\n"
                    if take_profit:
                        risk_text += f"🎯 Take Profit: ${take_profit:,.2f}"
                    
                    fields.append({
                        'name': '💼 Risk Management',
                        'value': risk_text,
                        'inline': False
                    })
            
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=color_map.get(new_signal, 0xffff00)
            )
            
        except Exception as e:
            logger.error(f"Failed to send signal change alert: {e}")
            return False
    
    async def send_trade_execution_alert(
        self,
        coin: str,
        action: str,
        amount: float,
        price: float,
        total_value: float,
        balance_usdt: float,
        balance_coin: float,
        position_status: str = "",
        trade_summary: str = ""
    ) -> bool:
        """
        Send trade execution alert to Discord
        
        Args:
            coin: Trading coin
            action: BUY or SELL
            amount: Amount traded
            price: Execution price
            total_value: Total value in USDT
            balance_usdt: Remaining USDT
            balance_coin: Remaining coin balance
            position_status: Current position description
            trade_summary: Trade summary message
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            action_emoji = '🟢' if action == 'BUY' else '🔴'
            color = 0x00ff00 if action == 'BUY' else 0xff0000
            
            title = f"{action_emoji} Trade Executed - {coin}"
            description = (
                f"**{action}** {amount:.6f} {coin}\n"
                f"**${price:,.2f}** per {coin}\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            fields = []
            
            # Trade details
            fields.append({
                'name': '💰 Trade Details',
                'value': (
                    f"Amount: {amount:.6f} {coin}\n"
                    f"Price: ${price:,.2f}\n"
                    f"Total: ${total_value:,.2f}"
                ),
                'inline': True
            })
            
            # Updated balances
            fields.append({
                'name': '💼 Updated Balances',
                'value': (
                    f"💵 USDT: ${balance_usdt:,.2f}\n"
                    f"🪙 {coin}: {balance_coin:.6f}"
                ),
                'inline': True
            })
            
            # Position status
            if not position_status:
                if balance_coin > 0.000001:
                    position_value = balance_coin * price
                    position_status = f"Holding {coin} (${position_value:,.2f})"
                else:
                    position_status = f"In USDT (no {coin} holdings)"
            
            fields.append({
                'name': '📊 Position Status',
                'value': position_status,
                'inline': False
            })
            
            # Trade summary
            if trade_summary:
                fields.append({
                    'name': '📈 Trade Summary',
                    'value': trade_summary[:1024],
                    'inline': False
                })
            
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=color
            )
            
        except Exception as e:
            logger.error(f"Failed to send trade execution alert: {e}")
            return False
    
    async def send_bot_status(
        self,
        status: str = "ONLINE",
        message: str = "Trading bot is running",
        trading_engine: str = "Active",
        market_data: str = "Connected",
        ai_analysis: str = "Running",
        risk_management: str = "Enabled",
        markets: str = "BTC/USD, SOL/USD",
        ai_models: str = "LLM Advisor + Deep Analyzer",
        update_interval: str = "5 seconds",
        deep_analysis_interval: str = "Every 2 hours",
        additional_info: str = ""
    ) -> bool:
        """
        Send bot status update to Discord
        
        Args:
            status: ONLINE, WARNING, or ERROR
            message: Status message
            ... (other status fields)
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            status_emoji = {
                'ONLINE': '✅',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'OFFLINE': '🔴'
            }
            
            color_map = {
                'ONLINE': 0x00ff00,
                'WARNING': 0xffff00,
                'ERROR': 0xff0000,
                'OFFLINE': 0x808080
            }
            
            emoji = status_emoji.get(status, '✅')
            
            title = f"{emoji} Trading Bot {status}"
            description = (
                f"{message}\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            fields = []
            
            # System status
            fields.append({
                'name': '🔧 System Status',
                'value': (
                    f"✅ Trading Engine: {trading_engine}\n"
                    f"✅ Market Data: {market_data}\n"
                    f"✅ AI Analysis: {ai_analysis}\n"
                    f"✅ Risk Management: {risk_management}"
                ),
                'inline': False
            })
            
            # Active monitoring
            fields.append({
                'name': '📊 Active Monitoring',
                'value': (
                    f"Markets: {markets}\n"
                    f"AI Models: {ai_models}\n"
                    f"Update Interval: {update_interval}"
                ),
                'inline': False
            })
            
            # Notification settings
            fields.append({
                'name': '🔔 Notification Settings',
                'value': (
                    f"✅ Signal Changes\n"
                    f"✅ Trade Executions\n"
                    f"✅ Deep Analysis ({deep_analysis_interval})\n"
                    f"✅ Error Alerts"
                ),
                'inline': False
            })
            
            if additional_info:
                fields.append({
                    'name': 'ℹ️ Additional Info',
                    'value': additional_info[:1024],
                    'inline': False
                })
            
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=color_map.get(status, 0x00ff00)
            )
            
        except Exception as e:
            logger.error(f"Failed to send bot status: {e}")
            return False
    
    async def send_error_alert(
        self,
        error_type: str,
        component: str,
        severity: str,
        error_description: str,
        impact: str,
        recommended_action: str,
        trading_status: str = "Unknown",
        monitoring_status: str = "Unknown",
        notification_status: str = "Active",
        additional_context: str = ""
    ) -> bool:
        """
        Send error alert to Discord
        
        Args:
            error_type: Type of error
            component: Component name
            severity: LOW, MEDIUM, HIGH, CRITICAL
            error_description: Error details
            impact: Impact description
            recommended_action: What user should do
            trading_status: Current trading status
            monitoring_status: Current monitoring status
            notification_status: Current notification status
            additional_context: Extra info
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            severity_emoji = {
                'LOW': '⚠️',
                'MEDIUM': '⚠️',
                'HIGH': '❌',
                'CRITICAL': '🚨'
            }
            
            severity_color = {
                'LOW': 0xffff00,
                'MEDIUM': 0xff9900,
                'HIGH': 0xff0000,
                'CRITICAL': 0x8b0000
            }
            
            emoji = severity_emoji.get(severity, '⚠️')
            
            title = f"{emoji} {error_type}"
            description = (
                f"Component: {component}\n"
                f"Severity: **{severity}**\n"
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            fields = []
            
            # Error details
            fields.append({
                'name': '❌ Error Details',
                'value': error_description[:1024],
                'inline': False
            })
            
            # Impact
            fields.append({
                'name': '⚠️ Impact',
                'value': impact[:1024],
                'inline': False
            })
            
            # Recommended action
            fields.append({
                'name': '💡 Recommended Action',
                'value': recommended_action[:1024],
                'inline': False
            })
            
            # System status
            status_emoji_map = {
                'Active': '✅',
                'Paused': '⏸️',
                'Stopped': '🛑',
                'Reconnecting': '🔄',
                'Unknown': '❓'
            }
            
            fields.append({
                'name': '🔧 System Status',
                'value': (
                    f"{status_emoji_map.get(trading_status, '❓')} Trading: {trading_status}\n"
                    f"{status_emoji_map.get(monitoring_status, '❓')} Monitoring: {monitoring_status}\n"
                    f"{status_emoji_map.get(notification_status, '❓')} Notifications: {notification_status}"
                ),
                'inline': False
            })
            
            if additional_context:
                fields.append({
                    'name': 'ℹ️ Additional Context',
                    'value': additional_context[:1024],
                    'inline': False
                })
            
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=severity_color.get(severity, 0xffff00)
            )
            
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")
            return False
    
    async def send_daily_summary(
        self,
        date: str,
        starting_balance: float,
        ending_balance: float,
        pnl: float,
        pnl_percent: float,
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        breakeven_trades: int,
        win_rate: float,
        avg_trade: float,
        best_trades: str,
        total_signals: int,
        signal_accuracy: float,
        ml_confidence_avg: float,
        current_positions: str,
        ai_insights: str,
        next_summary: str = "Tomorrow at 23:59"
    ) -> bool:
        """
        Send daily trading summary to Discord
        
        Args:
            date: Date string
            starting_balance: Starting balance
            ending_balance: Ending balance
            pnl: Profit/loss amount
            pnl_percent: P&L percentage
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            losing_trades: Number of losing trades
            breakeven_trades: Number of breakeven trades
            win_rate: Win rate percentage (0-1)
            avg_trade: Average trade result
            best_trades: Best trades text
            total_signals: Total signals generated
            signal_accuracy: Signal accuracy (0-1)
            ml_confidence_avg: Average ML confidence (0-1)
            current_positions: Current positions text
            ai_insights: AI-generated insights
            next_summary: Next summary time
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            pnl_emoji = '🟢' if pnl >= 0 else '🔴'
            pnl_sign = '+' if pnl >= 0 else ''
            color = 0x00ff00 if pnl >= 0 else 0xff0000
            
            title = "📊 Daily Trading Summary"
            description = (
                f"**{date}**\n"
                f"{datetime.now().strftime('%H:%M:%S')}"
            )
            
            fields = []
            
            # Performance
            fields.append({
                'name': '💰 Performance',
                'value': (
                    f"Starting: ${starting_balance:,.2f}\n"
                    f"Ending: ${ending_balance:,.2f}\n"
                    f"\n{pnl_emoji} **P&L: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)**"
                ),
                'inline': False
            })
            
            # Trading activity
            win_percent = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            lose_percent = (losing_trades / total_trades * 100) if total_trades > 0 else 0
            
            fields.append({
                'name': '📈 Trading Activity',
                'value': (
                    f"Total Trades: {total_trades}\n"
                    f"✅ Winning: {winning_trades} ({win_percent:.1f}%)\n"
                    f"❌ Losing: {losing_trades} ({lose_percent:.1f}%)\n"
                    f"🟡 Breakeven: {breakeven_trades}\n"
                    f"\nWin Rate: {win_rate:.1%}\n"
                    f"Avg Trade: ${avg_trade:,.2f}"
                ),
                'inline': True
            })
            
            # Market analysis
            fields.append({
                'name': '📊 Market Analysis',
                'value': (
                    f"Signals: {total_signals}\n"
                    f"Accuracy: {signal_accuracy:.1%}\n"
                    f"ML Confidence: {ml_confidence_avg:.1%}"
                ),
                'inline': True
            })
            
            # Best trades
            if best_trades:
                fields.append({
                    'name': '🎯 Best Trades',
                    'value': best_trades[:1024],
                    'inline': False
                })
            
            # Current positions
            fields.append({
                'name': '📍 Current Positions',
                'value': current_positions[:1024],
                'inline': False
            })
            
            # AI insights
            if ai_insights:
                fields.append({
                    'name': '🤖 AI Insights',
                    'value': ai_insights[:1024],
                    'inline': False
                })
            
            # Footer
            fields.append({
                'name': 'ℹ️ Next Summary',
                'value': next_summary,
                'inline': False
            })
            
            return await self.send_embed(
                title=title,
                description=description,
                fields=fields,
                color=color
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    async def close(self):
        """Close bot connection"""
        if self.enabled and self.bot:
            await self.bot.close()


# Global instance
_discord_bot_instance = None
_bot_task = None


async def get_discord_notifier() -> TradingDiscordBot:
    """Get or create Discord notifier instance"""
    global _discord_bot_instance, _bot_task
    
    if _discord_bot_instance is None:
        _discord_bot_instance = TradingDiscordBot()
        
        if _discord_bot_instance.enabled:
            # Start bot in background
            _bot_task = asyncio.create_task(
                _discord_bot_instance.bot.start(_discord_bot_instance.token)
            )
            
            # Wait for bot to be ready
            max_wait = 10  # seconds
            waited = 0
            while not _discord_bot_instance.is_ready and waited < max_wait:
                await asyncio.sleep(0.5)
                waited += 0.5
            
            if not _discord_bot_instance.is_ready:
                logger.warning("Discord bot took longer than expected to connect")
    
    return _discord_bot_instance

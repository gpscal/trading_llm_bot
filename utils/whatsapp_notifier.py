"""
WhatsApp Notification System via Twilio
Sends trading signal alerts and LLM advisor summaries to WhatsApp
Uses Message Templates for WhatsApp Business API compliance
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
from twilio.rest import Client
from utils.logger import setup_logger

logger = setup_logger('whatsapp_notifier', 'whatsapp_notifier.log')


class WhatsAppNotifier:
    """Sends trading notifications to WhatsApp via Twilio using Message Templates"""
    
    def __init__(
        self, 
        account_sid: Optional[str] = None, 
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        use_templates: Optional[bool] = None
    ):
        """
        Initialize WhatsApp notifier
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: Your Twilio WhatsApp number (format: whatsapp:+15558419388)
            to_number: Your WhatsApp number (format: whatsapp:+1234567890)
            use_templates: Force template usage (True for production, False for sandbox)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        
        # Support sandbox-specific env variables for testing
        # If TWILIO_WHATSAPP_FROM_SANDBOX is set, use sandbox mode
        from_sandbox = os.getenv('TWILIO_WHATSAPP_FROM_SANDBOX')
        if from_sandbox:
            self.from_number = from_number or from_sandbox
            self.to_number = to_number or os.getenv('TWILIO_WHATSAPP_TO_SANDBOX') or os.getenv('TWILIO_WHATSAPP_TO')
        else:
            self.from_number = from_number or os.getenv('TWILIO_WHATSAPP_FROM')
            self.to_number = to_number or os.getenv('TWILIO_WHATSAPP_TO')
        
        # Auto-detect or override template usage
        if use_templates is None:
            # Use templates if NOT using sandbox number
            self.use_templates = '+14155238886' not in str(self.from_number)
        else:
            self.use_templates = use_templates
        
        self.enabled = bool(
            self.account_sid and 
            self.auth_token and 
            self.from_number and 
            self.to_number
        )
        
        if not self.enabled:
            logger.warning(
                "WhatsApp notifier disabled - missing Twilio credentials: "
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, TWILIO_WHATSAPP_TO"
            )
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                mode = "template mode" if self.use_templates else "freeform mode"
                logger.info(f"WhatsApp notifier initialized (to: {self.to_number}, {mode})")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False
    
    def send_template_message(
        self, 
        template_name: str, 
        variables: Optional[Dict[str, str]] = None,
        content_sid: Optional[str] = None
    ) -> bool:
        """
        Send a message using a WhatsApp template
        
        Args:
            template_name: Name of the approved template
            variables: Variables to substitute in template (e.g., {"1": "BTC", "2": "75000"})
            content_sid: Optional Content SID (use either template_name or content_sid)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("WhatsApp disabled, skipping template message")
            return False
        
        try:
            msg_params = {
                'from_': self.from_number,
                'to': self.to_number
            }
            
            if content_sid:
                # Use Content Template (preferred method)
                msg_params['content_sid'] = content_sid
                if variables:
                    msg_params['content_variables'] = str(variables)
            else:
                # Use legacy template method
                msg_params['body'] = template_name
                if variables:
                    # Variables need to be passed differently for legacy templates
                    pass
            
            msg = self.client.messages.create(**msg_params)
            
            logger.info(f"WhatsApp template message sent successfully (SID: {msg.sid})")
            return True
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp template message: {e}")
            return False
    
    def send_message(self, message: str, fallback_to_simple: bool = True) -> bool:
        """
        Send a message to WhatsApp (uses template if in production mode)
        
        Args:
            message: Message text (plain text, WhatsApp doesn't support HTML)
            fallback_to_simple: If template fails, try sending as freeform (sandbox only)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("WhatsApp disabled, skipping message")
            return False
        
        # If using templates, send via generic notification template
        if self.use_templates:
            logger.warning(
                "Template mode enabled but sending freeform message. "
                "This will fail outside 24-hour window. "
                "Please use send_template_message() or specific alert methods with templates."
            )
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(f"WhatsApp message sent successfully (SID: {msg.sid})")
            return True
                
        except Exception as e:
            error_msg = str(e)
            if "63016" in error_msg or "allowed window" in error_msg:
                logger.error(
                    f"Failed to send WhatsApp message: Outside 24-hour window. "
                    f"You must use Message Templates for production WhatsApp numbers. "
                    f"Error: {e}"
                )
            else:
                logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    def send_signal_change_alert(
        self,
        coin: str,
        old_signal: str,
        new_signal: str,
        price: float,
        confidence: float,
        llm_signal: Optional[Dict[str, Any]] = None,
        deep_analysis: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a trading signal change alert
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            old_signal: Previous signal ('BUY', 'SELL', 'HOLD')
            new_signal: New signal ('BUY', 'SELL', 'HOLD')
            price: Current coin price
            confidence: Trading confidence score (0-1)
            llm_signal: LLM advisor signal data (optional)
            deep_analysis: Deep analyzer data (optional)
        
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        # Try using template first if available
        if self.use_templates:
            try:
                # Template variables (adjust based on your template structure)
                variables = {
                    "1": coin,
                    "2": new_signal,
                    "3": f"${price:,.2f}",
                    "4": f"{confidence:.0%}",
                    "5": old_signal
                }
                
                # Try to send using template
                # Note: You need to create this template in Twilio console first
                result = self.send_template_message(
                    template_name="signal_change_alert",
                    variables=variables
                )
                
                if result:
                    return True
                else:
                    logger.warning("Template send failed, falling back to freeform (may fail)")
            except Exception as e:
                logger.warning(f"Template method failed: {e}, trying freeform")
        
        # Fallback to freeform message (will fail outside 24-hour window in production)
        # Signal emoji mapping
        signal_emoji = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡'
        }
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message (plain text for WhatsApp)
        message = f"🚨 *SIGNAL CHANGE ALERT*\n"
        message += f"{'='*30}\n"
        message += f"*Coin:* {coin}\n"
        message += f"*Time:* {timestamp}\n"
        message += f"*Price:* ${price:,.2f}\n\n"
        
        # Signal change
        message += f"*Signal Change:*\n"
        message += f"{signal_emoji.get(old_signal, '⚪')} {old_signal} → {signal_emoji.get(new_signal, '⚪')} *{new_signal}*\n"
        message += f"*Confidence:* {confidence:.1%}\n\n"
        
        # LLM Advisor feedback
        if llm_signal:
            llm_signal_str = llm_signal.get('signal', 'HOLD')
            llm_confidence_str = llm_signal.get('confidence', 'UNKNOWN')
            llm_confidence_score = llm_signal.get('confidence_score', 0.0)
            llm_reasoning = llm_signal.get('reasoning', 'No reasoning provided')
            
            message += f"*🤖 LLM Advisor:*\n"
            message += f"{signal_emoji.get(llm_signal_str, '⚪')} Signal: *{llm_signal_str}*\n"
            message += f"📊 Confidence: {llm_confidence_str} ({llm_confidence_score:.1%})\n"
            message += f"💡 Analysis:\n_{llm_reasoning[:300]}_\n"
            
            # Add stop loss / take profit if available
            if llm_signal.get('stop_loss'):
                message += f"🛑 Stop Loss: ${llm_signal['stop_loss']:,.2f}\n"
            if llm_signal.get('take_profit'):
                message += f"🎯 Take Profit: ${llm_signal['take_profit']:,.2f}\n"
            
            message += "\n"
        
        # Deep Analysis feedback (if available)
        if deep_analysis:
            deep_signal = deep_analysis.get('signal', 'HOLD')
            deep_confidence = deep_analysis.get('confidence_score', 0.0)
            deep_summary = deep_analysis.get('summary', 'No summary available')
            
            message += f"*🔍 Deep Analysis:*\n"
            message += f"{signal_emoji.get(deep_signal, '⚪')} Signal: *{deep_signal}*\n"
            message += f"📊 Confidence: {deep_confidence:.1%}\n"
            message += f"📝 Summary:\n_{deep_summary[:250]}_\n\n"
        
        # Footer
        message += f"{'='*30}\n"
        message += f"_Trading Bot v1.0_"
        
        return self.send_message(message)
    
    def send_trade_execution_alert(
        self,
        coin: str,
        action: str,
        amount: float,
        price: float,
        total_value: float,
        balance_usdt: float,
        balance_coin: float
    ) -> bool:
        """
        Send trade execution notification
        
        Args:
            coin: Trading coin
            action: 'BUY' or 'SELL'
            amount: Amount of coin traded
            price: Execution price
            total_value: Total value in USDT
            balance_usdt: Remaining USDT balance
            balance_coin: Remaining coin balance
        """
        if not self.enabled:
            return False
        
        # Try using template first if available
        if self.use_templates:
            try:
                variables = {
                    "1": coin,
                    "2": action,
                    "3": f"{amount:.4f}",
                    "4": f"${price:,.2f}",
                    "5": f"${total_value:,.2f}",
                    "6": f"${balance_usdt:,.2f}"
                }
                
                result = self.send_template_message(
                    template_name="trade_execution_alert",
                    variables=variables
                )
                
                if result:
                    return True
            except Exception as e:
                logger.warning(f"Template method failed: {e}, trying freeform")
        
        # Fallback to freeform
        emoji = '🟢' if action == 'BUY' else '🔴'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"*{emoji} TRADE EXECUTED*\n"
        message += f"{'='*30}\n"
        message += f"*Action:* {action} {coin}\n"
        message += f"*Amount:* {amount:.4f} {coin}\n"
        message += f"*Price:* ${price:,.2f}\n"
        message += f"*Total:* ${total_value:,.2f}\n"
        message += f"*Time:* {timestamp}\n\n"
        message += f"*💰 Balance After Trade:*\n"
        message += f"USDT: ${balance_usdt:,.2f}\n"
        message += f"{coin}: {balance_coin:.6f}\n\n"
        
        # Add clear position status
        if balance_coin > 0.000001:
            position_value = balance_coin * price
            message += f"*📊 Position:* Holding {coin} (${position_value:,.2f})\n"
        else:
            message += f"*📊 Position:* In USDT (no {coin} holdings)\n"
        
        message += f"{'='*30}"
        
        return self.send_message(message)
    
    def send_error_alert(self, error_message: str, context: str = '') -> bool:
        """Send error notification"""
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"*⚠️ TRADING BOT ERROR*\n"
        message += f"{'='*30}\n"
        message += f"*Time:* {timestamp}\n"
        if context:
            message += f"*Context:* {context}\n"
        message += f"\n{error_message[:500]}\n"
        message += f"{'='*30}"
        
        return self.send_message(message)
    
    def send_deep_analysis_report(
        self,
        coin: str,
        price: float,
        analysis: Dict[str, Any]
    ) -> bool:
        """
        Send deep analysis report (every 2 hours)
        
        Args:
            coin: Trading coin (e.g., 'SOL', 'BTC')
            price: Current price
            analysis: Deep analysis result dictionary
        
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
            
            # Emoji mapping
            trend_emoji = {
                'BULLISH': '📈',
                'BEARISH': '📉',
                'NEUTRAL': '➡️'
            }
            action_emoji = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '🟡'
            }
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🔴'
            }
            
            # Format timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Build message
            message = f"📊 *DEEP MARKET ANALYSIS*\n"
            message += f"{'='*30}\n"
            message += f"*{coin}/USD* @ ${price:,.2f}\n"
            message += f"_{timestamp}_\n\n"
            
            # Main recommendation
            message += f"*📋 Recommendation:*\n"
            message += f"{action_emoji.get(action, '⚪')} *{action}* (Confidence: {confidence:.0%})\n"
            message += f"{trend_emoji.get(trend, '⚪')} Trend: *{trend}*\n"
            message += f"{risk_emoji.get(risk_level, '⚪')} Risk: {risk_level}\n\n"
            
            # Key indicators
            key_indicators = analysis.get('key_indicators', {})
            if key_indicators:
                message += f"*📈 Technical Indicators:*\n"
                
                rsi = key_indicators.get('rsi')
                if rsi:
                    rsi_status = "Oversold" if rsi < 30 else ("Overbought" if rsi > 70 else "Neutral")
                    message += f"RSI: {rsi:.1f} ({rsi_status})\n"
                
                adx = key_indicators.get('adx')
                if adx:
                    trend_strength = "Strong" if adx > 25 else "Weak"
                    message += f"ADX: {adx:.1f} ({trend_strength} trend)\n"
                
                volatility = key_indicators.get('volatility_ratio')
                if volatility:
                    vol_status = "High" if volatility > 0.02 else ("Low" if volatility < 0.01 else "Normal")
                    message += f"Volatility: {vol_status}\n"
                
                message += "\n"
            
            # Support/Resistance levels
            support = analysis.get('support_levels', [])
            resistance = analysis.get('resistance_levels', [])
            if support or resistance:
                message += f"*🎯 Key Levels:*\n"
                if support and len(support) > 0:
                    message += f"Support: ${support[0]:,.2f}\n"
                if resistance and len(resistance) > 0:
                    message += f"Resistance: ${resistance[0]:,.2f}\n"
                message += "\n"
            
            # Stop loss / Take profit suggestions
            stop_loss = analysis.get('stop_loss_suggestion')
            take_profit = analysis.get('take_profit_suggestion')
            if stop_loss or take_profit:
                message += f"*💼 Trade Levels:*\n"
                if stop_loss:
                    message += f"🛑 Stop Loss: ${stop_loss:,.2f}\n"
                if take_profit:
                    message += f"🎯 Take Profit: ${take_profit:,.2f}\n"
                message += "\n"
            
            # AI Reasoning (summarized)
            message += f"*🤖 AI Analysis:*\n"
            reasoning_summary = reasoning[:350]
            if len(reasoning) > 350:
                reasoning_summary = reasoning[:350] + "..."
            message += f"_{reasoning_summary}_\n\n"
            
            # Market Sentiment (Fear & Greed)
            sentiment_score = analysis.get('sentiment_score')
            if sentiment_score:
                sentiment_value = int(sentiment_score * 100)
                fg_classification = (
                    "Extreme Fear" if sentiment_value < 25 else
                    "Fear" if sentiment_value < 45 else
                    "Neutral" if sentiment_value < 55 else
                    "Greed" if sentiment_value < 75 else
                    "Extreme Greed"
                )
                message += f"*🌍 Market Sentiment:*\n"
                message += f"Fear & Greed: {sentiment_value}/100 ({fg_classification})\n\n"
            
            # News Sentiment Analysis
            news_summary = analysis.get('news_summary')
            if news_summary:
                message += f"*📰 News Analysis:*\n"
                
                # Get news sentiment label and score
                news_sentiment = None
                # Check if there's a news_sentiment field in the analysis
                # (from enhanced_data in deep_analyzer)
                if 'news_sentiment' in analysis:
                    news_sentiment = analysis['news_sentiment']
                
                if news_sentiment:
                    sentiment_label = news_sentiment.get('label', 'NEUTRAL')
                    sentiment_emoji = {
                        'BULLISH': '📰🟢',
                        'BEARISH': '📰🔴',
                        'NEUTRAL': '📰⚪'
                    }
                    article_count = news_sentiment.get('article_count', 0)
                    
                    message += f"{sentiment_emoji.get(sentiment_label, '📰⚪')} *{sentiment_label}*\n"
                    message += f"From {article_count} articles\n\n"
                    
                    # Add top headlines if available
                    headlines = news_sentiment.get('top_headlines', [])
                    if headlines:
                        message += f"_Recent Headlines:_\n"
                        for i, headline in enumerate(headlines[:3], 1):
                            title = headline.get('title', 'No title')
                            # Truncate long headlines
                            if len(title) > 70:
                                title = title[:67] + "..."
                            message += f"• {title}\n"
                        message += "\n"
                else:
                    # Just show the summary if we don't have full sentiment data
                    message += f"_{news_summary}_\n\n"
            
            # Patterns and Warnings
            patterns = analysis.get('key_patterns', [])
            warnings = analysis.get('warnings', [])
            if patterns or warnings:
                message += f"*⚠️ Key Patterns & Warnings:*\n"
                for pattern in patterns[:3]:  # Top 3 patterns
                    message += f"• {pattern}\n"
                for warning in warnings[:2]:  # Top 2 warnings
                    message += f"⚠️ {warning}\n"
                message += "\n"
            
            # Footer
            message += f"{'='*30}\n"
            model_used = analysis.get('ai_model_used', 'AI')
            message += f"_Analyzed by {model_used}_\n"
            message += f"_Next update in ~2 hours_"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send deep analysis report: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test WhatsApp connection"""
        if not self.enabled:
            logger.error("Cannot test - WhatsApp not configured")
            return False
        
        try:
            test_msg = (
                f"*✅ Bot Connected*\n\n"
                f"WhatsApp notifications are working!\n"
                f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            )
            result = self.send_message(test_msg)
            
            if result:
                logger.info("✅ WhatsApp test message sent successfully")
            else:
                logger.error("❌ WhatsApp test message failed")
            
            return result
                
        except Exception as e:
            logger.error(f"WhatsApp test failed: {e}")
            return False


# Global instance
_whatsapp_notifier_instance = None


def get_whatsapp_notifier(
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    from_number: Optional[str] = None,
    to_number: Optional[str] = None
) -> WhatsAppNotifier:
    """Get or create WhatsApp notifier instance"""
    global _whatsapp_notifier_instance
    
    if _whatsapp_notifier_instance is None:
        _whatsapp_notifier_instance = WhatsAppNotifier(
            account_sid, auth_token, from_number, to_number
        )
    
    return _whatsapp_notifier_instance

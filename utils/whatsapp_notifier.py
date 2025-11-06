"""
WhatsApp Notification System via Twilio
Sends trading signal alerts and LLM advisor summaries to WhatsApp
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
from twilio.rest import Client
from utils.logger import setup_logger

logger = setup_logger('whatsapp_notifier', 'whatsapp_notifier.log')


class WhatsAppNotifier:
    """Sends trading notifications to WhatsApp via Twilio"""
    
    def __init__(
        self, 
        account_sid: Optional[str] = None, 
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None
    ):
        """
        Initialize WhatsApp notifier
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            from_number: Your Twilio WhatsApp number (format: whatsapp:+14155238886)
            to_number: Your WhatsApp number (format: whatsapp:+1234567890)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = from_number or os.getenv('TWILIO_WHATSAPP_FROM')
        self.to_number = to_number or os.getenv('TWILIO_WHATSAPP_TO')
        
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
                logger.info(f"WhatsApp notifier initialized (to: {self.to_number})")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.enabled = False
    
    def send_message(self, message: str) -> bool:
        """
        Send a message to WhatsApp
        
        Args:
            message: Message text (plain text, WhatsApp doesn't support HTML)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("WhatsApp disabled, skipping message")
            return False
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            
            logger.info(f"WhatsApp message sent successfully (SID: {msg.sid})")
            return True
                
        except Exception as e:
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
        Send a trading signal change alert with LLM advisor feedback
        
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
        
        # Signal emoji mapping
        signal_emoji = {
            'BUY': '??',
            'SELL': '??',
            'HOLD': '??'
        }
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message (plain text for WhatsApp)
        message = f"?? *SIGNAL CHANGE ALERT*\n"
        message += f"{'='*30}\n"
        message += f"*Coin:* {coin}\n"
        message += f"*Time:* {timestamp}\n"
        message += f"*Price:* ${price:,.2f}\n\n"
        
        # Signal change
        message += f"*Signal Change:*\n"
        message += f"{signal_emoji.get(old_signal, '?')} {old_signal} ? {signal_emoji.get(new_signal, '?')} *{new_signal}*\n"
        message += f"*Confidence:* {confidence:.1%}\n\n"
        
        # LLM Advisor feedback
        if llm_signal:
            llm_signal_str = llm_signal.get('signal', 'HOLD')
            llm_confidence_str = llm_signal.get('confidence', 'UNKNOWN')
            llm_confidence_score = llm_signal.get('confidence_score', 0.0)
            llm_reasoning = llm_signal.get('reasoning', 'No reasoning provided')
            
            message += f"*?? LLM Advisor:*\n"
            message += f"{signal_emoji.get(llm_signal_str, '?')} Signal: *{llm_signal_str}*\n"
            message += f"?? Confidence: {llm_confidence_str} ({llm_confidence_score:.1%})\n"
            message += f"?? Analysis:\n_{llm_reasoning[:300]}_\n"
            
            # Add stop loss / take profit if available
            if llm_signal.get('stop_loss'):
                message += f"??? Stop Loss: ${llm_signal['stop_loss']:,.2f}\n"
            if llm_signal.get('take_profit'):
                message += f"?? Take Profit: ${llm_signal['take_profit']:,.2f}\n"
            
            message += "\n"
        
        # Deep Analysis feedback (if available)
        if deep_analysis:
            deep_signal = deep_analysis.get('signal', 'HOLD')
            deep_confidence = deep_analysis.get('confidence_score', 0.0)
            deep_summary = deep_analysis.get('summary', 'No summary available')
            
            message += f"*?? Deep Analysis:*\n"
            message += f"{signal_emoji.get(deep_signal, '?')} Signal: *{deep_signal}*\n"
            message += f"?? Confidence: {deep_confidence:.1%}\n"
            message += f"?? Summary:\n_{deep_summary[:250]}_\n\n"
        
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
        
        emoji = '??' if action == 'BUY' else '??'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"*{emoji} TRADE EXECUTED*\n"
        message += f"{'='*30}\n"
        message += f"*Action:* {action} {coin}\n"
        message += f"*Amount:* {amount:.4f} {coin}\n"
        message += f"*Price:* ${price:,.2f}\n"
        message += f"*Total:* ${total_value:,.2f}\n"
        message += f"*Time:* {timestamp}\n\n"
        message += f"*?? Balance:*\n"
        message += f"USDT: ${balance_usdt:,.2f}\n"
        message += f"{coin}: {balance_coin:.6f}\n"
        message += f"{'='*30}"
        
        return self.send_message(message)
    
    def send_error_alert(self, error_message: str, context: str = '') -> bool:
        """Send error notification"""
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"*?? TRADING BOT ERROR*\n"
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
            macro_trend = analysis.get('macro_trend', 'Unknown')
            
            # Emoji mapping
            trend_emoji = {
                'BULLISH': '??',
                'BEARISH': '??',
                'NEUTRAL': '??'
            }
            action_emoji = {
                'BUY': '??',
                'SELL': '??',
                'HOLD': '??'
            }
            risk_emoji = {
                'LOW': '??',
                'MEDIUM': '??',
                'HIGH': '??'
            }
            
            # Format timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Build message
            message = f"?? *DEEP MARKET ANALYSIS*\n"
            message += f"{'='*30}\n"
            message += f"*{coin}/USD* @ ${price:,.2f}\n"
            message += f"_{timestamp}_\n\n"
            
            # Main recommendation
            message += f"*?? Recommendation:*\n"
            message += f"{action_emoji.get(action, '?')} *{action}* (Confidence: {confidence:.0%})\n"
            message += f"{trend_emoji.get(trend, '?')} Trend: *{trend}*\n"
            message += f"{risk_emoji.get(risk_level, '?')} Risk: {risk_level}\n\n"
            
            # Key indicators
            key_indicators = analysis.get('key_indicators', {})
            if key_indicators:
                message += f"*?? Technical Indicators:*\n"
                
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
                message += f"*?? Key Levels:*\n"
                if support and len(support) > 0:
                    message += f"Support: ${support[0]:,.2f}\n"
                if resistance and len(resistance) > 0:
                    message += f"Resistance: ${resistance[0]:,.2f}\n"
                message += "\n"
            
            # Stop loss / Take profit suggestions
            stop_loss = analysis.get('stop_loss_suggestion')
            take_profit = analysis.get('take_profit_suggestion')
            if stop_loss or take_profit:
                message += f"*?? Trade Levels:*\n"
                if stop_loss:
                    message += f"??? Stop Loss: ${stop_loss:,.2f}\n"
                if take_profit:
                    message += f"?? Take Profit: ${take_profit:,.2f}\n"
                message += "\n"
            
            # Key patterns
            patterns = analysis.get('key_patterns', [])
            if patterns:
                message += f"*?? Patterns:* {', '.join(patterns[:3])}\n\n"
            
            # Market sentiment
            sentiment = analysis.get('sentiment_score')
            if sentiment:
                sentiment_pct = int(sentiment * 100)
                sentiment_status = (
                    "Extreme Fear" if sentiment_pct < 25 else
                    "Fear" if sentiment_pct < 45 else
                    "Neutral" if sentiment_pct < 55 else
                    "Greed" if sentiment_pct < 75 else
                    "Extreme Greed"
                )
                message += f"*?? Market Sentiment:*\n"
                message += f"Fear & Greed: {sentiment_pct}/100 ({sentiment_status})\n\n"
            
            # AI Reasoning (summarized)
            message += f"*?? AI Analysis:*\n"
            # Truncate reasoning to fit WhatsApp limits (max ~300 chars for reasoning)
            reasoning_summary = reasoning[:350]
            if len(reasoning) > 350:
                reasoning_summary = reasoning[:350] + "..."
            message += f"_{reasoning_summary}_\n\n"
            
            # Macro trend
            if macro_trend and macro_trend != 'Unknown':
                message += f"*?? Macro Outlook:*\n"
                macro_summary = macro_trend[:200]
                if len(macro_trend) > 200:
                    macro_summary = macro_trend[:200] + "..."
                message += f"_{macro_summary}_\n\n"
            
            # Warnings
            warnings = analysis.get('warnings', [])
            if warnings:
                message += f"*?? Warnings:*\n"
                for warning in warnings[:2]:  # Max 2 warnings
                    message += f"• {warning[:100]}\n"
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
                f"*? Bot Connected*\n\n"
                f"WhatsApp notifications are working!\n"
                f"_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            )
            result = self.send_message(test_msg)
            
            if result:
                logger.info("? WhatsApp test message sent successfully")
            else:
                logger.error("? WhatsApp test message failed")
            
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

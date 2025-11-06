"""
Telegram Bot Notification System
Sends trading signal alerts and LLM advisor summaries to Telegram
"""
import os
import asyncio
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger('telegram_notifier', 'telegram_notifier.log')


class TelegramNotifier:
    """Sends trading notifications to Telegram"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_API')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
        if not self.enabled:
            logger.warning("Telegram notifier disabled - missing TELEGRAM_API or TELEGRAM_CHAT_ID")
        else:
            logger.info(f"Telegram notifier initialized (chat_id: {self.chat_id})")
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """
        Send a message to Telegram
        
        Args:
            message: Message text (supports HTML or Markdown formatting)
            parse_mode: 'HTML' or 'Markdown'
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram disabled, skipping message")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
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
        
        # Build message header
        message = f"<b>?? Signal Change Alert</b>\n"
        message += f"??????????????????\n"
        message += f"<b>Coin:</b> {coin}\n"
        message += f"<b>Time:</b> {timestamp}\n"
        message += f"<b>Price:</b> ${price:,.2f}\n\n"
        
        # Signal change
        message += f"<b>Signal Change:</b>\n"
        message += f"{signal_emoji.get(old_signal, '?')} {old_signal} ? {signal_emoji.get(new_signal, '?')} <b>{new_signal}</b>\n"
        message += f"<b>Confidence:</b> {confidence:.1%}\n\n"
        
        # LLM Advisor feedback
        if llm_signal:
            llm_signal_str = llm_signal.get('signal', 'HOLD')
            llm_confidence_str = llm_signal.get('confidence', 'UNKNOWN')
            llm_confidence_score = llm_signal.get('confidence_score', 0.0)
            llm_reasoning = llm_signal.get('reasoning', 'No reasoning provided')
            
            message += f"<b>?? LLM Advisor:</b>\n"
            message += f"{signal_emoji.get(llm_signal_str, '?')} Signal: <b>{llm_signal_str}</b>\n"
            message += f"?? Confidence: {llm_confidence_str} ({llm_confidence_score:.1%})\n"
            message += f"?? Analysis:\n<i>{llm_reasoning[:300]}</i>\n"
            
            # Add stop loss / take profit if available
            if llm_signal.get('stop_loss'):
                message += f"?? Stop Loss: ${llm_signal['stop_loss']:,.2f}\n"
            if llm_signal.get('take_profit'):
                message += f"?? Take Profit: ${llm_signal['take_profit']:,.2f}\n"
            
            message += "\n"
        
        # Deep Analysis feedback (if available)
        if deep_analysis:
            deep_signal = deep_analysis.get('signal', 'HOLD')
            deep_confidence = deep_analysis.get('confidence_score', 0.0)
            deep_summary = deep_analysis.get('summary', 'No summary available')
            
            message += f"<b>?? Deep Analysis:</b>\n"
            message += f"{signal_emoji.get(deep_signal, '?')} Signal: <b>{deep_signal}</b>\n"
            message += f"?? Confidence: {deep_confidence:.1%}\n"
            message += f"?? Summary:\n<i>{deep_summary[:250]}</i>\n\n"
        
        # Footer
        message += f"??????????????????\n"
        message += f"<i>Trading Bot v1.0</i>"
        
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
        
        message = f"<b>{emoji} Trade Executed</b>\n"
        message += f"??????????????????\n"
        message += f"<b>Action:</b> {action} {coin}\n"
        message += f"<b>Amount:</b> {amount:.4f} {coin}\n"
        message += f"<b>Price:</b> ${price:,.2f}\n"
        message += f"<b>Total:</b> ${total_value:,.2f}\n"
        message += f"<b>Time:</b> {timestamp}\n\n"
        message += f"<b>?? Balance:</b>\n"
        message += f"USDT: ${balance_usdt:,.2f}\n"
        message += f"{coin}: {balance_coin:.6f}\n"
        message += f"??????????????????"
        
        return self.send_message(message)
    
    def send_error_alert(self, error_message: str, context: str = '') -> bool:
        """Send error notification"""
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"<b>?? Trading Bot Error</b>\n"
        message += f"??????????????????\n"
        message += f"<b>Time:</b> {timestamp}\n"
        if context:
            message += f"<b>Context:</b> {context}\n"
        message += f"\n<code>{error_message[:500]}</code>\n"
        message += f"??????????????????"
        
        return self.send_message(message)
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.enabled:
            logger.error("Cannot test - Telegram not configured")
            return False
        
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                bot_name = bot_info.get('result', {}).get('username', 'Unknown')
                logger.info(f"? Telegram bot connected: @{bot_name}")
                
                # Send test message
                test_msg = f"<b>? Bot Connected</b>\n\nTelegram notifications are working!\n<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
                self.send_message(test_msg)
                return True
            else:
                logger.error(f"Telegram connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram test failed: {e}")
            return False


# Global instance
_telegram_notifier_instance = None


def get_telegram_notifier(bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> TelegramNotifier:
    """Get or create Telegram notifier instance"""
    global _telegram_notifier_instance
    
    if _telegram_notifier_instance is None:
        _telegram_notifier_instance = TelegramNotifier(bot_token, chat_id)
    
    return _telegram_notifier_instance

"""
LLM Trading Advisor - Uses local Ollama with DeepSeek-R1 for fast trading signals
Provides LLM-based trading signals that complement existing indicators
"""
import os
import sys
import asyncio
import aiohttp
import time
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path for Trading LLM Bot imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.logger import setup_logger
from utils.shared_state import append_log_safe

logger = setup_logger('llm_advisor_logger', 'llm_advisor.log')

# Cache for LLM responses to avoid excessive API calls
_llm_cache = {}
_cache_duration = 600  # 10 minutes cache (increased from 5 to prevent rapid signal changes)
_last_call_time = 0
_min_call_interval = 300  # Minimum 5 minutes between calls (aligns with poll interval)


class LLMAdvisor:
    """LLM-based trading advisor using local Ollama with DeepSeek-R1"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('llm_enabled', False)
        self.ollama_base_url = config.get('ollama_base_url', 'http://localhost:11434')
        self.model = config.get('ollama_model', 'deepseek-r1:8b')
        self.timeout = config.get('ollama_timeout', 120)  # 2 minutes for slower models
        self._session = None
        self._initialized = False
        
        if self.enabled:
            self._initialized = True
            logger.info(f"LLM Advisor initialized with Ollama model: {self.model} (timeout: {self.timeout}s)")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    def _build_trading_prompt(
        self,
        coin: str,
        price: float,
        indicators: Dict[str, Any],
        balance_usdt: float,
        balance_coin: float
    ) -> str:
        """Build a concise trading analysis prompt for the LLM"""
        
        # Extract key indicators
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', [0, 0])
        macd_line = macd[0] if isinstance(macd, (list, tuple)) else 0
        macd_signal = macd[1] if isinstance(macd, (list, tuple)) and len(macd) > 1 else 0
        adx = indicators.get('adx', 20)
        atr = indicators.get('atr', 0)
        moving_avg = indicators.get('moving_avg', price)
        momentum = indicators.get('momentum', 0)
        obv = indicators.get('obv', 0)
        
        # Bollinger bands
        bb = indicators.get('bollinger_bands', [price * 1.02, price * 0.98])
        bb_upper = bb[0] if isinstance(bb, (list, tuple)) else price * 1.02
        bb_lower = bb[1] if isinstance(bb, (list, tuple)) and len(bb) > 1 else price * 0.98
        
        # Stochastic
        stoch = indicators.get('stochastic_oscillator', 50)
        if isinstance(stoch, (list, tuple)):
            stoch = stoch[0]
        
        prompt = f"""You are a cryptocurrency trading analyst. Analyze the following market data for {coin}/USD and provide a trading recommendation.

CURRENT MARKET DATA:
- Price: ${price:,.2f}
- 14-period Moving Average: ${moving_avg:,.2f}
- Price vs MA: {((price / moving_avg - 1) * 100):.2f}%

TECHNICAL INDICATORS:
- RSI (14): {rsi:.1f} (Oversold <30, Overbought >70)
- MACD Line: {macd_line:.2f}
- MACD Signal: {macd_signal:.2f}
- MACD Histogram: {(macd_line - macd_signal):.2f}
- ADX (Trend Strength): {adx:.1f} (Strong >25)
- ATR (Volatility): ${atr:.2f}
- Stochastic: {stoch:.1f}
- OBV Trend: {"Positive" if obv > 0 else "Negative"}
- Bollinger Upper: ${bb_upper:,.2f}
- Bollinger Lower: ${bb_lower:,.2f}

PORTFOLIO:
- USDT Balance: ${balance_usdt:,.2f}
- {coin} Holdings: {balance_coin:.6f} (${balance_coin * price:,.2f})

Based on this analysis, provide your recommendation in the following exact format:

SIGNAL: [BUY/SELL/HOLD]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [One sentence explanation]
STOP_LOSS: [Price level or N/A]
TAKE_PROFIT: [Price level or N/A]

Important: Only output the recommendation in the format above. Be decisive - choose BUY, SELL, or HOLD based on the indicators."""

        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract trading signal"""
        result = {
            'signal': 'HOLD',
            'confidence': 'LOW',
            'confidence_score': 0.2,
            'reasoning': '',
            'stop_loss': None,
            'take_profit': None,
            'full_analysis': response
        }
        
        # Handle DeepSeek-R1's <think>...</think> tags - extract content after thinking
        if '<think>' in response:
            # Find content after </think> tag
            think_end = response.find('</think>')
            if think_end != -1:
                response_to_parse = response[think_end + 8:].strip()
            else:
                response_to_parse = response
        else:
            response_to_parse = response
        
        # Extract SIGNAL
        signal_match = re.search(r'SIGNAL:\s*(BUY|SELL|HOLD)', response_to_parse, re.IGNORECASE)
        if signal_match:
            result['signal'] = signal_match.group(1).upper()
        
        # Extract CONFIDENCE
        confidence_match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', response_to_parse, re.IGNORECASE)
        if confidence_match:
            confidence = confidence_match.group(1).upper()
            result['confidence'] = confidence
            confidence_map = {'HIGH': 0.8, 'MEDIUM': 0.5, 'LOW': 0.2}
            result['confidence_score'] = confidence_map.get(confidence, 0.5)
        
        # Extract REASONING
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=STOP_LOSS:|TAKE_PROFIT:|$)', response_to_parse, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            result['reasoning'] = reasoning_match.group(1).strip()[:500]
        
        # Extract STOP_LOSS
        stop_loss_match = re.search(r'STOP_LOSS:\s*\$?([\d,]+\.?\d*)', response_to_parse, re.IGNORECASE)
        if stop_loss_match:
            try:
                result['stop_loss'] = float(stop_loss_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        # Extract TAKE_PROFIT
        take_profit_match = re.search(r'TAKE_PROFIT:\s*\$?([\d,]+\.?\d*)', response_to_parse, re.IGNORECASE)
        if take_profit_match:
            try:
                result['take_profit'] = float(take_profit_match.group(1).replace(',', ''))
            except ValueError:
                pass
        
        return result
    
    async def get_trading_signal(
        self,
        sol_price: float,
        btc_price: float,
        btc_indicators: Dict[str, Any],
        sol_indicators: Dict[str, Any],
        balance_usdt: float,
        balance_sol: float,
        sol_historical: Optional[List] = None,
        btc_historical: Optional[List] = None,
        selected_coin: str = 'SOL'
    ) -> Optional[Dict[str, Any]]:
        """
        Get LLM trading signal based on current market conditions
        
        Returns:
            {
                'signal': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 'HIGH' | 'MEDIUM' | 'LOW',
                'confidence_score': 0.0-1.0,
                'reasoning': str,
                'stop_loss': float (optional),
                'take_profit': float (optional)
            }
        """
        if not self.enabled or not self._initialized:
            logger.warning("LLM advisor not enabled or not initialized - returning None")
            return None
        
        # Rate limiting - check cache and minimum interval
        global _last_call_time
        current_time = time.time()
        
        # Create cache key based on time bucket only
        time_bucket = int(current_time / _cache_duration)
        cache_key = f"llm_signal_{time_bucket}"
        time_since_last_call = current_time - _last_call_time
        
        # Check cache first
        if cache_key in _llm_cache:
            cached_result = _llm_cache[cache_key]
            cache_age = current_time - cached_result['timestamp']
            if cache_age < _cache_duration:
                logger.debug(f"Using cached LLM response (age: {cache_age:.1f}s)")
                result = cached_result['result'].copy()
                result['is_cached'] = True
                return result
        
        # Enforce minimum call interval
        if time_since_last_call < _min_call_interval:
            for key, cached_data in _llm_cache.items():
                cache_age = current_time - cached_data['timestamp']
                if cache_age < _cache_duration:
                    logger.debug(f"LLM throttled, returning cached signal (age: {cache_age:.1f}s)")
                    result = cached_data['result'].copy()
                    result['is_cached'] = True
                    return result
            
            logger.info(f"LLM call throttled (minimum {_min_call_interval}s interval, {time_since_last_call:.1f}s since last call)")
            return None
        
        try:
            # Select appropriate data based on coin
            selected_coin = selected_coin.upper()
            if selected_coin == 'BTC':
                price = btc_price
                indicators = btc_indicators
                balance_coin = balance_sol  # This is actually the BTC balance passed in
            else:
                price = sol_price
                indicators = sol_indicators
                balance_coin = balance_sol
            
            # Build prompt
            prompt = self._build_trading_prompt(
                coin=selected_coin,
                price=price,
                indicators=indicators,
                balance_usdt=balance_usdt,
                balance_coin=balance_coin
            )
            
            # Update last call time BEFORE making the call
            _last_call_time = current_time
            logger.info(f"Calling Ollama ({self.model}) for {selected_coin} trading analysis...")
            
            # Call Ollama API
            session = await self._get_session()
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent responses
                    "num_predict": 500   # Limit response length
                }
            }
            
            start_time = time.time()
            async with session.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload
            ) as response:
                elapsed = time.time() - start_time
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API error (status {response.status}): {error_text[:200]}")
                    return None
                
                data = await response.json()
                llm_response = data.get('response', '')
                
                logger.info(f"Ollama response received in {elapsed:.1f}s")
                logger.debug(f"Raw LLM response: {llm_response[:500]}...")
            
            # Parse response
            result = self._parse_llm_response(llm_response)
            result['is_cached'] = False
            
            # Cache result
            _llm_cache[cache_key] = {
                'timestamp': current_time,
                'result': result
            }
            
            # Clean old cache entries
            self._clean_cache()
            
            logger.info(f"LLM Signal for {selected_coin}: {result['signal']}, Confidence: {result['confidence']} ({result['confidence_score']:.2f})")
            append_log_safe(f"LLM [{selected_coin}]: {result['signal']} ({result['confidence']}, score: {result['confidence_score']:.2f})")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting LLM trading signal: {e}", exc_info=True)
            return None
    
    def _clean_cache(self):
        """Remove old cache entries"""
        global _llm_cache
        current_time = time.time()
        keys_to_remove = [
            k for k, v in _llm_cache.items()
            if current_time - v['timestamp'] > _cache_duration
        ]
        for k in keys_to_remove:
            del _llm_cache[k]
    
    async def close(self):
        """Cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()


# Global instance
_llm_advisor_instance = None

def get_llm_advisor(config: Optional[Dict[str, Any]] = None) -> Optional[LLMAdvisor]:
    """Get or create LLM advisor instance"""
    global _llm_advisor_instance
    
    if config is None:
        from config.config import CONFIG
        config = CONFIG
    
    if _llm_advisor_instance is None:
        _llm_advisor_instance = LLMAdvisor(config)
    
    return _llm_advisor_instance

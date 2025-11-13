"""
LLM Trading Advisor - Integrates LLM_trader with Trading LLM Bot
Provides LLM-based trading signals that complement existing indicators
"""
import os
import sys
import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Add parent directory to path for Trading LLM Bot imports (must be before LLM_trader)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import Trading LLM Bot utilities first
from utils.logger import setup_logger
from utils.shared_state import append_log_safe

# Add LLM_trader to path (after Trading LLM Bot imports to avoid conflicts)
llm_trader_path = os.path.join(os.path.dirname(__file__), '..', 'LLM_trader')
if llm_trader_path not in sys.path:
    sys.path.insert(0, llm_trader_path)

logger = setup_logger('llm_advisor_logger', 'llm_advisor.log')

# Cache for LLM responses to avoid excessive API calls
_llm_cache = {}
_cache_duration = 600  # 10 minutes cache (increased from 5 to prevent rapid signal changes)
_last_call_time = 0
_min_call_interval = 300  # Minimum 5 minutes between calls (increased from 60s to align with cooldown)


class LLMAdvisor:
    """LLM-based trading advisor that integrates with Trading LLM Bot"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('llm_enabled', False)
        self.model_manager = None
        self.prompt_builder = None
        self.extractor = None
        self._initialized = False
        
        if self.enabled:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Lazy initialization of LLM components"""
        if self._initialized:
            return
        
        try:
            llm_trader_dir = os.path.abspath(llm_trader_path)
            
            # CRITICAL: Change working directory to LLM_trader so relative imports work
            # and add it to sys.path, removing conflicting paths
            original_cwd = os.getcwd()
            original_path = sys.path.copy()
            
            # Preserve all paths but reorder: LLM_trader first, remove Trading LLM Bot parent_dir
            # Keep venv paths (site-packages) for dependencies
            # Just reorder instead of replacing completely
            
            # Remove Trading LLM Bot parent_dir temporarily
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
            
            # Ensure LLM_trader is first
            if llm_trader_dir in sys.path:
                sys.path.remove(llm_trader_dir)
            sys.path.insert(0, llm_trader_dir)
            
            try:
                # Change to LLM_trader directory so relative imports resolve correctly
                os.chdir(llm_trader_dir)
                
                # Clear any cached imports that might interfere
                import importlib
                modules_to_clear = [k for k in list(sys.modules.keys()) if any(x in k for x in ['core.', 'utils.', 'logger.'])]
                for mod_name in modules_to_clear:
                    if not mod_name.startswith('_'):
                        try:
                            del sys.modules[mod_name]
                        except (KeyError, AttributeError):
                            pass
                
                # Import LLM_trader utils modules using absolute paths to avoid conflicts
                # We need to import them from LLM_trader's utils, not Trading LLM Bot's
                import importlib.util
                
                # Load utils.dataclass first (model_manager needs it)
                dataclass_path = os.path.join(llm_trader_dir, 'utils', 'dataclass.py')
                spec = importlib.util.spec_from_file_location('llm_utils_dataclass', dataclass_path)
                utils_dataclass_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(utils_dataclass_module)
                sys.modules['utils.dataclass'] = utils_dataclass_module
                
                # Load utils.position_extractor
                extractor_path = os.path.join(llm_trader_dir, 'utils', 'position_extractor.py')
                spec = importlib.util.spec_from_file_location('llm_utils_position_extractor', extractor_path)
                utils_extractor_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(utils_extractor_module)
                sys.modules['utils.position_extractor'] = utils_extractor_module
                
                # Now import core modules - they should be able to find utils modules
                from core.model_manager import ModelManager
                from core.trading_prompt import TradingPromptBuilder
                from utils.position_extractor import PositionExtractor
                from utils.dataclass import PromptContext, TechnicalSnapshot, MarketPeriod, MarketData, SentimentData, ResponseBuffer
                from logger.logger import Logger as LLMLogger
                
                # Store classes for later use
                self._ModelManager = ModelManager
                self._TradingPromptBuilder = TradingPromptBuilder
                self._PositionExtractor = PositionExtractor
                self._LLMLogger = LLMLogger
                self._PromptContext = PromptContext
                self._TechnicalSnapshot = TechnicalSnapshot
                self._MarketPeriod = MarketPeriod
                self._MarketData = MarketData
                self._SentimentData = SentimentData
                self._ResponseBuffer = ResponseBuffer
                
                # Initialize ModelManager while still in LLM_trader directory
                # ModelManager looks for config/model_config.ini relative to current directory
                model_config_relative = 'config/model_config.ini'
                if not os.path.exists(model_config_relative):
                    raise FileNotFoundError(f"LLM model config file not found: {os.path.abspath(model_config_relative)}")
                
                # Initialize logger
                llm_logger = LLMLogger(logger_name="LLMAdvisor", logger_debug=False)
                
                # ModelManager's config_path parameter is for the main config.ini file
                main_config_path = 'config/config.ini'
                config_path_to_pass = main_config_path if os.path.exists(main_config_path) else 'config'
                
                # Initialize ModelManager (MUST happen while in LLM_trader directory)
                self.model_manager = ModelManager(llm_logger, config_path=config_path_to_pass)
                self.prompt_builder = TradingPromptBuilder(llm_logger)
                self.extractor = PositionExtractor()
                
            finally:
                # Restore working directory and path AFTER ModelManager is initialized
                os.chdir(original_cwd)
                sys.path[:] = original_path
                # Keep LLM_trader accessible for future use
                if llm_trader_dir not in sys.path:
                    sys.path.insert(0, llm_trader_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
            
            self._initialized = True
            logger.info("LLM Advisor initialized successfully")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            # Use module-level logger
            from utils.logger import setup_logger as _setup_logger
            _logger = _setup_logger('llm_advisor_logger', 'llm_advisor.log')
            _logger.error(f"Failed to initialize LLM Advisor: {e}\n{error_details}")
            self.enabled = False
            self._initialized = False
    
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
        
        # Create cache key based on time bucket only (not price-sensitive)
        # This allows reusing the same response for the cache duration regardless of small price changes
        time_bucket = int(current_time / _cache_duration)
        cache_key = f"llm_signal_{time_bucket}"
        time_since_last_call = current_time - _last_call_time
        
        # Check cache first - if we have a recent response, use it
        if cache_key in _llm_cache:
            cached_result = _llm_cache[cache_key]
            cache_age = current_time - cached_result['timestamp']
            if cache_age < _cache_duration:
                logger.debug(f"Using cached LLM response (age: {cache_age:.1f}s)")
                # Mark result as cached so trade logic knows not to recheck stability
                result = cached_result['result'].copy()
                result['is_cached'] = True
                return result
        
        # Enforce minimum call interval - but still return cached signal if available
        if time_since_last_call < _min_call_interval:
            # Check if we have ANY recent cached result (not just current time bucket)
            for key, cached_data in _llm_cache.items():
                cache_age = current_time - cached_data['timestamp']
                if cache_age < _cache_duration:
                    logger.debug(f"LLM throttled, returning cached signal (age: {cache_age:.1f}s)")
                    result = cached_data['result'].copy()
                    result['is_cached'] = True
                    return result
            
            # No cache available and throttled - return None
            logger.info(f"LLM call throttled (minimum {_min_call_interval}s interval, {time_since_last_call:.1f}s since last call), no cache available")
            return None
        
        try:
            # Build prompt context from Trading LLM Bot data
            logger.debug(f"Building LLM prompt context for {selected_coin}...")
            prompt_context = self._build_prompt_context(
                sol_price, btc_price, btc_indicators, sol_indicators,
                balance_usdt, balance_sol, sol_historical, btc_historical,
                selected_coin=selected_coin
            )
            
            # Build prompt
            logger.debug("Building LLM prompt...")
            prompt = self.prompt_builder.build_prompt(prompt_context)
            
            # Update last call time BEFORE making the call to prevent rapid retries
            _last_call_time = current_time
            logger.info(f"Calling LLM for trading analysis... (last call was {time_since_last_call:.1f}s ago)")
            
            # Use stored ResponseBuffer from initialization
            ResponseBuffer = self._ResponseBuffer
            buffer = ResponseBuffer()
            logger.debug("Sending prompt to LLM model...")
            analysis = await self.model_manager.send_prompt(prompt, buffer)
            
            # Extract trading signal from LLM response
            signal, confidence_str, stop_loss, take_profit, position_size = self.extractor.extract_trading_info(analysis)
            
            # Convert confidence string to score
            confidence_map = {'HIGH': 0.8, 'MEDIUM': 0.5, 'LOW': 0.2}
            confidence_score = confidence_map.get(confidence_str, 0.5)
            
            result = {
                'signal': signal,
                'confidence': confidence_str,
                'confidence_score': confidence_score,
                'reasoning': analysis[:500],  # First 500 chars of reasoning
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'full_analysis': analysis,
                'is_cached': False  # Fresh signal from LLM
            }
            
            # Cache result
            _llm_cache[cache_key] = {
                'timestamp': current_time,
                'result': result
            }
            
            # Clean old cache entries
            self._clean_cache()
            
            logger.info(f"LLM Signal for {selected_coin}: {signal}, Confidence: {confidence_str} ({confidence_score:.2f})")
            append_log_safe(f"LLM [{selected_coin}]: {signal} ({confidence_str}, score: {confidence_score:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting LLM trading signal: {e}", exc_info=True)
            return None
    
    def _build_prompt_context(
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
    ):
        """Build LLM prompt context from Trading LLM Bot data structures"""
        # Use stored classes from initialization
        PromptContext = self._PromptContext
        TechnicalSnapshot = self._TechnicalSnapshot
        MarketPeriod = self._MarketPeriod
        MarketData = self._MarketData
        SentimentData = self._SentimentData
        
        # Select the appropriate indicators and price based on selected_coin
        selected_coin = selected_coin.upper()
        if selected_coin == 'BTC':
            primary_indicators = btc_indicators
            primary_price = btc_price
            primary_balance = balance_sol  # Note: This is actually the coin balance, not specifically SOL
            symbol = "BTC/USD"
        else:  # Default to SOL
            primary_indicators = sol_indicators
            primary_price = sol_price
            primary_balance = balance_sol
            symbol = "SOL/USD"
        
        logger.debug(f"Building prompt context for {symbol} (price: {primary_price})")
        
        # Skip OHLCV candles for now - the LLM works fine without detailed candle data
        # The technical indicators provide sufficient market context
        ohlcv_candles = None
        logger.debug("Skipping OHLCV candles (using indicators only)")
        
        # Build technical snapshot from indicators
        try:
            # Safely extract bollinger bands
            bb_bands = primary_indicators.get('bollinger_bands')
            if bb_bands and isinstance(bb_bands, (list, tuple)) and len(bb_bands) >= 3:
                bb_upper, bb_middle, bb_lower = float(bb_bands[0]), float(bb_bands[1]), float(bb_bands[2])
            else:
                bb_upper, bb_middle, bb_lower = primary_price * 1.02, primary_price, primary_price * 0.98
            
            # Safely extract MACD
            macd = primary_indicators.get('macd')
            if macd and isinstance(macd, (list, tuple)) and len(macd) >= 2:
                macd_line, macd_signal = float(macd[0]), float(macd[1])
                macd_hist = macd_line - macd_signal
            else:
                macd_line, macd_signal, macd_hist = 0.0, 0.0, 0.0
            
            # Safely extract stochastic
            stoch = primary_indicators.get('stochastic_oscillator')
            if stoch and isinstance(stoch, (list, tuple)) and len(stoch) >= 2:
                stoch_k, stoch_d = float(stoch[0]), float(stoch[1])
            else:
                stoch_k, stoch_d = 50.0, 50.0
            
            technical_snapshot = TechnicalSnapshot(
                vwap_5m=float(primary_indicators.get('vwap', primary_price)),
                twap=float(primary_indicators.get('twap', primary_price)),
                mfi_14=float(primary_indicators.get('mfi', 50.0)),
                obv=float(primary_indicators.get('obv', 0)),
                cmf=float(primary_indicators.get('cmf', 0)),
                force_index=float(primary_indicators.get('force_index', 0)),
                
                rsi_5m_14=float(primary_indicators.get('rsi', 50.0)),
                macd_line=macd_line,
                macd_signal=macd_signal,
                macd_hist=macd_hist,
                stoch_k=stoch_k,
                stoch_d=stoch_d,
                williams_r=float(primary_indicators.get('williams_r', -50)),
                
                adx=float(primary_indicators.get('adx', 20)),
                plus_di=float(primary_indicators.get('plus_di', 20)),
                minus_di=float(primary_indicators.get('minus_di', 20)),
                supertrend=float(primary_price),  # Simplified
                supertrend_direction=1.0,
                psar=float(primary_price),  # Simplified
                
                atr_5m_14=float(primary_indicators.get('atr', primary_price * 0.02)),
                bb_upper=bb_upper,
                bb_middle=bb_middle,
                bb_lower=bb_lower,
                
                hurst=0.5,  # Not calculated in Trading LLM Bot
                kurtosis=0.0,  # Not calculated in Trading LLM Bot
                zscore=0.0  # Not calculated in Trading LLM Bot
            )
        except Exception as e:
            logger.warning(f"Error building technical snapshot for {selected_coin}: {e}", exc_info=True)
            # Fallback minimal snapshot
            technical_snapshot = TechnicalSnapshot(
                vwap_5m=primary_price, twap=primary_price, mfi_14=50, obv=0, cmf=0, force_index=0,
                rsi_5m_14=primary_indicators.get('rsi', 50), macd_line=0, macd_signal=0, macd_hist=0,
                stoch_k=50, stoch_d=50, williams_r=-50,
                adx=20, plus_di=20, minus_di=20, supertrend=primary_price, supertrend_direction=1.0, psar=primary_price,
                atr_5m_14=primary_price * 0.02, bb_upper=primary_price, bb_middle=primary_price, bb_lower=primary_price,
                hurst=0.5, kurtosis=0.0, zscore=0.0
            )
        
        # Build market periods with proper metrics
        # Create minimal MarketData entries for metrics calculation
        current_market_data = MarketData(
            timestamp=datetime.now(),
            open=primary_price,
            high=primary_price * 1.01,  # Estimate
            low=primary_price * 0.99,   # Estimate
            close=primary_price,
            volume=1000000.0  # Estimate
        )
        
        # Create periods with data (MarketPeriod calculates metrics from data)
        market_metrics = {
            '1D': MarketPeriod(data=[current_market_data] * 48, period_name='1D'),  # 48 hours
            '2D': MarketPeriod(data=[current_market_data] * 72, period_name='2D'),  # 72 hours
            '3D': MarketPeriod(data=[current_market_data] * 730, period_name='3D')  # 730 hours (~1 month)
        }
        
        # Build context
        context = PromptContext(
            symbol=symbol,
            current_price=primary_price,
            ohlcv_candles=ohlcv_candles,
            technical_data=technical_snapshot,
            market_metrics=market_metrics,
            current_position=None,  # Trading LLM Bot doesn't track positions in this format
            sentiment=None,  # Optional - could fetch Fear & Greed Index
            trade_history=[],
            previous_response=""
        )
        
        return context
    
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
        """Cleanup LLM resources"""
        if self.model_manager:
            await self.model_manager.close()


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

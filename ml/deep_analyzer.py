"""
Deep Market Analyzer - Comprehensive analysis using Claude AI + RAG
Provides detailed market analysis to complement fast LLM_Advisor signals
"""
import os
import sys
import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.logger import setup_logger
from utils.shared_state import append_log_safe

logger = setup_logger('deep_analyzer_logger', 'deep_analyzer.log')


@dataclass
class DeepAnalysisResult:
    """Structured result from deep analysis"""
    timestamp: str
    symbol: str
    timeframe: str
    
    # Primary recommendation
    trend: str  # BULLISH, BEARISH, NEUTRAL
    recommended_action: str  # BUY, SELL, HOLD
    confidence: float  # 0.0-1.0
    
    # Technical analysis
    support_levels: List[float]
    resistance_levels: List[float]
    key_indicators: Dict[str, Any]
    divergences: List[Dict[str, Any]]
    
    # Market context
    sentiment_score: Optional[float]  # Fear & Greed Index
    news_summary: Optional[str]
    news_sentiment: Optional[Dict[str, Any]]  # News sentiment data from NewsAPI.ai
    macro_trend: str  # Long-term trend assessment
    
    # Risk assessment
    risk_level: str  # LOW, MEDIUM, HIGH
    stop_loss_suggestion: Optional[float]
    take_profit_suggestion: Optional[float]
    
    # AI reasoning
    reasoning: str
    key_patterns: List[str]
    warnings: List[str]
    
    # Metadata
    analysis_duration: float
    ai_model_used: str
    
    def to_dict(self):
        return asdict(self)


class DeepAnalyzer:
    """
    Deep market analysis engine using Claude AI and RAG system
    Runs less frequently (every 1-4 hours) but provides comprehensive context
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('deep_analysis_enabled', False)
        
        # API configuration
        self.anthropic_api_key = config.get('anthropic_api_key', os.getenv('ANTHROPIC_API_KEY'))
        self.openrouter_api_key = config.get('openrouter_api_key', os.getenv('OPENROUTER_API_KEY'))
        
        # Model configuration
        self.primary_model = config.get('deep_analysis_model', 'claude-3-5-sonnet-20241022')
        self.fallback_model = config.get('deep_analysis_fallback_model', 'anthropic/claude-3.5-sonnet')
        
        # Analysis settings
        self.analysis_interval = config.get('deep_analysis_interval', 7200)  # 2 hours default
        self.cache_duration = config.get('deep_analysis_cache_duration', 7200)
        
        # Cache
        self._cache = {}
        self._last_analysis_time = {}
        
        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"DeepAnalyzer initialized (enabled: {self.enabled}, model: {self.primary_model}, interval: {self.analysis_interval}s)")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Cleanup resources"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_analysis(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, Any],
        historical_data: Optional[List] = None,
        force_refresh: bool = False
    ) -> Optional[DeepAnalysisResult]:
        """
        Get comprehensive market analysis (cached)
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD', 'SOL/USD')
            current_price: Current market price
            indicators: Dictionary of technical indicators
            historical_data: Historical OHLCV data
            force_refresh: Force new analysis (ignore cache)
        
        Returns:
            DeepAnalysisResult or None if unavailable
        """
        if not self.enabled:
            logger.debug("Deep analyzer not enabled")
            return None
        
        # Check cache
        cache_key = f"{symbol}_{int(current_price)}"
        current_time = time.time()
        
        if not force_refresh and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cache_age = current_time - cached_result['timestamp']
            
            if cache_age < self.cache_duration:
                logger.info(f"Using cached deep analysis for {symbol} (age: {cache_age:.1f}s)")
                return DeepAnalysisResult(**cached_result['result'])
        
        # Check if enough time has passed since last analysis
        last_analysis = self._last_analysis_time.get(symbol, 0)
        time_since_last = current_time - last_analysis
        
        if not force_refresh and time_since_last < self.analysis_interval:
            logger.info(f"Deep analysis throttled for {symbol} (next in {self.analysis_interval - time_since_last:.0f}s)")
            return None
        
        try:
            start_time = time.time()
            logger.info(f"Starting deep analysis for {symbol} at ${current_price:.2f}")
            
            # Step 1: Gather enhanced data
            enhanced_data = await self._gather_enhanced_data(symbol, current_price, indicators, historical_data)
            
            # Step 2: Calculate advanced indicators
            advanced_indicators = self._calculate_advanced_indicators(indicators, historical_data)
            
            # Step 3: Detect divergences and patterns
            divergences = self._detect_divergences(indicators, historical_data)
            patterns = self._detect_patterns(indicators, historical_data)
            
            # Step 4: Get AI analysis
            ai_analysis = await self._get_ai_analysis(
                symbol, current_price, indicators, advanced_indicators,
                divergences, patterns, enhanced_data
            )
            
            if not ai_analysis:
                logger.warning(f"AI analysis failed for {symbol}")
                return None
            
            # Step 5: Build structured result
            result = self._build_analysis_result(
                symbol, current_price, indicators, advanced_indicators,
                divergences, patterns, enhanced_data, ai_analysis,
                time.time() - start_time
            )
            
            # Cache result
            self._cache[cache_key] = {
                'timestamp': current_time,
                'result': result.to_dict()
            }
            self._last_analysis_time[symbol] = current_time
            
            logger.info(f"Deep analysis completed for {symbol}: {result.recommended_action} "
                       f"(confidence: {result.confidence:.2f}, trend: {result.trend})")
            append_log_safe(f"?? Deep Analysis [{symbol}]: {result.recommended_action} "
                          f"({result.confidence:.0%} confidence, {result.trend})")
            
            # Send Discord notification with analysis report
            try:
                from utils.discord_notifier import get_discord_notifier
                discord_notifier = await get_discord_notifier()
                
                if discord_notifier.enabled:
                    # Extract coin from symbol (e.g., "BTC/USD" -> "BTC")
                    coin = symbol.split('/')[0] if '/' in symbol else symbol
                    
                    # Send report
                    sent = await discord_notifier.send_deep_analysis_report(
                        coin=coin,
                        price=current_price,
                        analysis=result.to_dict()
                    )
                    
                    if sent:
                        logger.info(f"💬 Deep analysis report sent to Discord for {symbol}")
                    else:
                        logger.debug("Discord notification not sent (may be disabled)")
            except Exception as e:
                logger.warning(f"Failed to send Discord notification: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in deep analysis for {symbol}: {e}", exc_info=True)
            return None
    
    async def _gather_enhanced_data(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, Any],
        historical_data: Optional[List]
    ) -> Dict[str, Any]:
        """Gather additional context data (sentiment, news, etc.)"""
        enhanced_data = {
            'fear_greed_index': None,
            'news_summary': None,
            'news_sentiment': None,
            'market_metrics': {}
        }
        
        try:
            # Fetch Fear & Greed Index and News in parallel for better performance
            fear_greed_task = self._fetch_fear_greed_index()
            news_task = self._fetch_crypto_news(symbol)
            
            # Await both tasks
            fear_greed, news_data = await asyncio.gather(
                fear_greed_task,
                news_task,
                return_exceptions=True
            )
            
            # Handle Fear & Greed result
            if isinstance(fear_greed, Exception):
                logger.warning(f"Error fetching Fear & Greed: {fear_greed}")
                fear_greed = None
            enhanced_data['fear_greed_index'] = fear_greed
            
            # Handle News result
            if isinstance(news_data, Exception):
                logger.warning(f"Error fetching news: {news_data}")
                news_data = None
            
            if news_data:
                enhanced_data['news_summary'] = news_data.get('summary')
                enhanced_data['news_sentiment'] = {
                    'score': news_data.get('sentiment_score', 0.0),
                    'label': news_data.get('sentiment_label', 'NEUTRAL'),
                    'article_count': news_data.get('article_count', 0),
                    'top_headlines': news_data.get('top_headlines', [])
                }
                logger.debug(f"News sentiment for {symbol}: {news_data.get('sentiment_label')} "
                           f"(score: {news_data.get('sentiment_score', 0):.2f})")
            
            logger.debug(f"Enhanced data gathered for {symbol}: "
                        f"Fear&Greed={fear_greed}, "
                        f"News={news_data.get('sentiment_label') if news_data else 'N/A'}")
            
        except Exception as e:
            logger.warning(f"Error gathering enhanced data: {e}")
        
        return enhanced_data
    
    async def _fetch_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """Fetch Fear & Greed Index from Alternative.me API"""
        try:
            session = await self._get_session()
            async with session.get('https://api.alternative.me/fng/', timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and len(data['data']) > 0:
                        fng = data['data'][0]
                        return {
                            'value': int(fng['value']),
                            'classification': fng['value_classification'],
                            'timestamp': fng['timestamp']
                        }
        except Exception as e:
            logger.debug(f"Failed to fetch Fear & Greed Index: {e}")
        
        return None
    
    async def _fetch_crypto_news(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cryptocurrency news from CryptoCompare (primary) or NewsAPI.ai (fallback)
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD', 'SOL/USD')
        
        Returns:
            Dictionary containing news summary, sentiment, and article count
        """
        # Check if news API is enabled and configured
        if not self.config.get('news_api_enabled', False):
            logger.debug("News API not enabled")
            return None
        
        # Check cache first
        cache_key = f"news_{symbol}"
        current_time = time.time()
        cache_duration = self.config.get('news_api_cache_duration', 3600)
        
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if current_time - cached_data.get('timestamp', 0) < cache_duration:
                logger.debug(f"Using cached news data for {symbol}")
                return cached_data.get('data')
        
        # Extract coin name from symbol (e.g., 'BTC/USD' -> 'BTC')
        coin = symbol.split('/')[0].upper()
        
        # Try CryptoCompare first (primary source)
        cryptocompare_result = await self._fetch_cryptocompare_news(coin)
        if cryptocompare_result:
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': current_time,
                'data': cryptocompare_result
            }
            logger.info(f"Fetched news from CryptoCompare for {symbol}: "
                       f"{cryptocompare_result['sentiment_label']} sentiment "
                       f"(score: {cryptocompare_result['sentiment_score']:.2f})")
            return cryptocompare_result
        
        # Fallback to NewsAPI.ai if CryptoCompare fails
        logger.info(f"CryptoCompare unavailable, falling back to NewsAPI.ai for {symbol}")
        newsapi_result = await self._fetch_newsapi_news(coin, symbol)
        if newsapi_result:
            # Cache the result
            self._cache[cache_key] = {
                'timestamp': current_time,
                'data': newsapi_result
            }
            logger.info(f"Fetched news from NewsAPI.ai for {symbol}: "
                       f"{newsapi_result['sentiment_label']} sentiment "
                       f"(score: {newsapi_result['sentiment_score']:.2f})")
            return newsapi_result
        
        logger.warning(f"All news sources failed for {symbol}")
        return None
    
    async def _fetch_cryptocompare_news(self, coin: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cryptocurrency news from CryptoCompare API
        
        Args:
            coin: Coin symbol (e.g., 'BTC', 'SOL')
        
        Returns:
            Dictionary containing news summary, sentiment, and article count
        """
        cryptocompare_api_key = self.config.get('cryptocompare_api_key')
        if not cryptocompare_api_key:
            logger.debug("CryptoCompare API key not configured (CRYPTOCOMPARE_API_KEY)")
            return None
        
        try:
            base_url = self.config.get('cryptocompare_base_url', 'https://min-api.cryptocompare.com/data')
            timeout = self.config.get('news_api_timeout', 15)
            
            # CryptoCompare news API endpoint
            url = f"{base_url}/v2/news/"
            params = {
                'categories': coin,
                'lang': 'EN'
            }
            
            # Add API key to headers
            headers = {
                'authorization': f'Apikey {cryptocompare_api_key}'
            }
            
            session = await self._get_session()
            
            logger.debug(f"Fetching CryptoCompare news for {coin}")
            
            async with session.get(url, params=params, headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"CryptoCompare API returned status {response.status}: {error_text[:200]}")
                    return None
                
                data = await response.json()
                
                # Parse CryptoCompare response
                if 'Data' not in data or not data['Data']:
                    logger.debug(f"No articles found in CryptoCompare response for {coin}")
                    return None
                
                articles = data['Data']
                
                # Limit to max articles
                max_articles = self.config.get('news_api_max_articles', 10)
                articles = articles[:max_articles]
                
                # Analyze sentiment from articles
                sentiment_analysis = self._analyze_news_sentiment(articles, coin, source='cryptocompare')
                
                # Build result
                result = {
                    'article_count': len(articles),
                    'sentiment_score': sentiment_analysis['sentiment_score'],
                    'sentiment_label': sentiment_analysis['sentiment_label'],
                    'summary': sentiment_analysis['summary'],
                    'top_headlines': [
                        {
                            'title': article.get('title', ''),
                            'source': article.get('source', 'Unknown'),
                            'url': article.get('url', ''),
                            'date': article.get('published_on', '')
                        }
                        for article in articles[:5]
                    ],
                    'timestamp': time.time(),
                    'news_source': 'CryptoCompare'
                }
                
                return result
                
        except asyncio.TimeoutError:
            logger.warning(f"CryptoCompare API request timed out for {coin}")
        except Exception as e:
            logger.warning(f"Error fetching CryptoCompare news for {coin}: {e}", exc_info=True)
        
        return None
    
    async def _fetch_newsapi_news(self, coin: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch cryptocurrency news from NewsAPI.ai (fallback)
        
        Args:
            coin: Coin symbol (e.g., 'BTC', 'SOL')
            symbol: Trading pair (e.g., 'BTC/USD', 'SOL/USD')
        
        Returns:
            Dictionary containing news summary, sentiment, and article count
        """
        news_api_key = self.config.get('news_api_key')
        if not news_api_key:
            logger.debug("NewsAPI.ai key not configured (NEWS_API_AI)")
            return None
        
        try:
            coin_keywords = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'SOL': 'solana',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'MATIC': 'polygon'
            }
            
            # Get primary keyword for this coin, fallback to generic crypto
            primary_keyword = coin_keywords.get(coin, 'cryptocurrency')
            
            # NewsAPI.ai query parameters
            base_url = self.config.get('news_api_base_url', 'https://eventregistry.org/api/v1')
            max_articles = self.config.get('news_api_max_articles', 10)
            timeout = self.config.get('news_api_timeout', 15)
            
            # Build request for recent articles
            session = await self._get_session()
            
            # NewsAPI.ai article search endpoint
            url = f"{base_url}/article/getArticles"
            params = {
                'apiKey': news_api_key,
                'keyword': primary_keyword,
                'articlesPage': 1,
                'articlesCount': max_articles,
                'articlesSortBy': 'date',
                'articlesSortByAsc': 'false',
                'lang': 'eng',
                'isDuplicateFilter': 'skipDuplicates',
                'resultType': 'articles'
            }
            
            logger.debug(f"Fetching NewsAPI.ai news for {symbol} (keyword: {primary_keyword})")
            
            async with session.get(url, params=params, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.warning(f"NewsAPI.ai returned status {response.status}: {error_text[:200]}")
                    return None
                
                data = await response.json()
                
                # Parse NewsAPI.ai response
                if 'articles' not in data or 'results' not in data['articles']:
                    logger.debug(f"No articles found in NewsAPI.ai response for {symbol}")
                    return None
                
                articles = data['articles']['results']
                
                if not articles or len(articles) == 0:
                    logger.debug(f"No articles returned for {symbol}")
                    return None
                
                # Analyze sentiment from articles
                sentiment_analysis = self._analyze_news_sentiment(articles, coin, source='newsapi')
                
                # Build result
                result = {
                    'article_count': len(articles),
                    'sentiment_score': sentiment_analysis['sentiment_score'],
                    'sentiment_label': sentiment_analysis['sentiment_label'],
                    'summary': sentiment_analysis['summary'],
                    'top_headlines': [
                        {
                            'title': article.get('title', ''),
                            'source': article.get('source', {}).get('title', 'Unknown'),
                            'url': article.get('url', ''),
                            'date': article.get('dateTime', '')
                        }
                        for article in articles[:5]
                    ],
                    'timestamp': time.time(),
                    'news_source': 'NewsAPI.ai'
                }
                
                return result
                
        except asyncio.TimeoutError:
            logger.warning(f"NewsAPI.ai request timed out for {symbol}")
        except Exception as e:
            logger.warning(f"Error fetching NewsAPI.ai news for {symbol}: {e}", exc_info=True)
        
        return None
    
    def _analyze_news_sentiment(self, articles: List[Dict], coin: str, source: str = 'newsapi') -> Dict[str, Any]:
        """
        Analyze sentiment from news articles
        
        Args:
            articles: List of article data from CryptoCompare or NewsAPI.ai
            coin: Coin symbol (e.g., 'BTC', 'SOL')
            source: Data source ('cryptocompare' or 'newsapi')
        
        Returns:
            Dictionary with sentiment score, label, and summary
        """
        if not articles:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'NEUTRAL',
                'summary': 'No recent news available'
            }
        
        # Sentiment keywords (simple keyword-based analysis)
        bullish_keywords = [
            'surge', 'rally', 'gain', 'rise', 'bull', 'bullish', 'soar', 'pump',
            'breakout', 'growth', 'profit', 'adoption', 'upgrade', 'milestone',
            'positive', 'optimistic', 'breakthrough', 'success', 'innovation'
        ]
        
        bearish_keywords = [
            'crash', 'plunge', 'drop', 'fall', 'bear', 'bearish', 'dump', 'decline',
            'loss', 'sell-off', 'panic', 'fear', 'scam', 'hack', 'regulation',
            'negative', 'concern', 'risk', 'warning', 'investigation'
        ]
        
        sentiment_scores = []
        headlines = []
        
        for article in articles:
            # Handle different article formats from different sources
            if source == 'cryptocompare':
                title = article.get('title', '').lower()
                body = article.get('body', '').lower()[:500]  # First 500 chars of body
            else:  # newsapi
                title = article.get('title', '').lower()
                body = article.get('body', '').lower()[:500]  # First 500 chars of body
            
            text = f"{title} {body}"
            
            # Count sentiment keywords
            bullish_count = sum(1 for keyword in bullish_keywords if keyword in text)
            bearish_count = sum(1 for keyword in bearish_keywords if keyword in text)
            
            # Calculate article sentiment score (-1 to 1)
            total_count = bullish_count + bearish_count
            if total_count > 0:
                article_sentiment = (bullish_count - bearish_count) / total_count
            else:
                article_sentiment = 0.0  # Neutral if no keywords found
            
            sentiment_scores.append(article_sentiment)
            headlines.append(article.get('title', 'Untitled'))
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        
        # Classify sentiment
        if avg_sentiment > 0.2:
            sentiment_label = 'BULLISH'
        elif avg_sentiment < -0.2:
            sentiment_label = 'BEARISH'
        else:
            sentiment_label = 'NEUTRAL'
        
        # Generate summary
        summary = f"Analyzed {len(articles)} recent articles. "
        if sentiment_label == 'BULLISH':
            summary += "Overall sentiment is positive with mentions of gains, adoption, and growth."
        elif sentiment_label == 'BEARISH':
            summary += "Overall sentiment is negative with concerns about declines, risks, or regulations."
        else:
            summary += "Mixed or neutral sentiment in recent news coverage."
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_label': sentiment_label,
            'summary': summary
        }
    
    def _calculate_advanced_indicators(
        self,
        indicators: Dict[str, Any],
        historical_data: Optional[List]
    ) -> Dict[str, Any]:
        """Calculate advanced technical indicators not in basic set"""
        advanced = {
            'volatility_ratio': 0.0,
            'trend_strength': 0.0,
            'volume_profile': 'normal',
            'momentum_divergence': False
        }
        
        try:
            # Volatility analysis
            atr = indicators.get('atr', 0)
            if atr > 0:
                # Normalize ATR by price for comparison
                # Higher ratio = higher volatility
                advanced['volatility_ratio'] = atr / indicators.get('vwap', 1.0)
            
            # Trend strength (using ADX)
            adx = indicators.get('adx', 0)
            if adx > 25:
                advanced['trend_strength'] = min(1.0, adx / 50.0)
            else:
                advanced['trend_strength'] = adx / 25.0
            
            # Volume analysis
            obv = indicators.get('obv', 0)
            if obv > 1000:
                advanced['volume_profile'] = 'high'
            elif obv < 100:
                advanced['volume_profile'] = 'low'
            
        except Exception as e:
            logger.debug(f"Error calculating advanced indicators: {e}")
        
        return advanced
    
    def _detect_divergences(
        self,
        indicators: Dict[str, Any],
        historical_data: Optional[List]
    ) -> List[Dict[str, Any]]:
        """Detect bullish/bearish divergences in indicators"""
        divergences = []
        
        # For initial implementation, we'll use simple heuristics
        # TODO: Implement full divergence detection from DiscordCryptoAnalyzer
        
        try:
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', (0, 0))
            macd_line, macd_signal = macd[0] if isinstance(macd, (list, tuple)) and len(macd) >= 1 else 0, \
                                      macd[1] if isinstance(macd, (list, tuple)) and len(macd) >= 2 else 0
            
            # RSI oversold/overbought with MACD confirmation
            if rsi < 30 and macd_line < macd_signal:
                divergences.append({
                    'type': 'bullish',
                    'indicator': 'RSI+MACD',
                    'confidence': 'medium',
                    'description': 'RSI oversold with MACD bearish - potential reversal'
                })
            elif rsi > 70 and macd_line > macd_signal:
                divergences.append({
                    'type': 'bearish',
                    'indicator': 'RSI+MACD',
                    'confidence': 'medium',
                    'description': 'RSI overbought with MACD bullish - potential reversal'
                })
            
        except Exception as e:
            logger.debug(f"Error detecting divergences: {e}")
        
        return divergences
    
    def _detect_patterns(
        self,
        indicators: Dict[str, Any],
        historical_data: Optional[List]
    ) -> List[str]:
        """Detect chart patterns and technical setups"""
        patterns = []
        
        try:
            # Bollinger Band squeeze
            bb = indicators.get('bollinger_bands')
            if bb and isinstance(bb, (list, tuple)) and len(bb) >= 3:
                bb_upper, bb_middle, bb_lower = bb[0], bb[1], bb[2]
                bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
                
                if bb_width < 0.04:  # Tight squeeze
                    patterns.append('bollinger_squeeze')
            
            # Strong trend
            adx = indicators.get('adx', 0)
            if adx > 40:
                patterns.append('strong_trend')
            
            # Momentum shift
            macd = indicators.get('macd', (0, 0))
            if isinstance(macd, (list, tuple)) and len(macd) >= 2:
                macd_line, macd_signal = macd[0], macd[1]
                if abs(macd_line - macd_signal) < 0.1:
                    patterns.append('macd_convergence')
            
        except Exception as e:
            logger.debug(f"Error detecting patterns: {e}")
        
        return patterns
    
    async def _get_ai_analysis(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, Any],
        advanced_indicators: Dict[str, Any],
        divergences: List[Dict[str, Any]],
        patterns: List[str],
        enhanced_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get AI analysis from Claude API"""
        try:
            # Build comprehensive prompt
            prompt = self._build_analysis_prompt(
                symbol, current_price, indicators, advanced_indicators,
                divergences, patterns, enhanced_data
            )
            
            # Try primary provider (Anthropic Claude)
            result = await self._call_anthropic_api(prompt)
            
            if result:
                return result
            
            # Fallback to OpenRouter
            logger.info("Primary API failed, trying OpenRouter fallback...")
            result = await self._call_openrouter_api(prompt)
            
            if result:
                return result
            
            # Fallback to local LLM_Advisor analysis (minimal)
            logger.warning("All AI providers failed, using minimal analysis")
            return self._build_fallback_analysis(indicators)
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}", exc_info=True)
            return None
    
    def _build_analysis_prompt(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, Any],
        advanced_indicators: Dict[str, Any],
        divergences: List[Dict[str, Any]],
        patterns: List[str],
        enhanced_data: Dict[str, Any]
    ) -> str:
        """Build comprehensive analysis prompt for Claude"""
        
        # Format indicators
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', (0, 0))
        macd_line = macd[0] if isinstance(macd, (list, tuple)) and len(macd) >= 1 else 0
        macd_signal = macd[1] if isinstance(macd, (list, tuple)) and len(macd) >= 2 else 0
        adx = indicators.get('adx', 0)
        obv = indicators.get('obv', 0)
        
        bb = indicators.get('bollinger_bands', (current_price, current_price, current_price))
        bb_upper = bb[0] if isinstance(bb, (list, tuple)) and len(bb) >= 1 else current_price
        bb_middle = bb[1] if isinstance(bb, (list, tuple)) and len(bb) >= 2 else current_price
        bb_lower = bb[2] if isinstance(bb, (list, tuple)) and len(bb) >= 3 else current_price
        
        stoch = indicators.get('stochastic_oscillator', (50, 50))
        stoch_k = stoch[0] if isinstance(stoch, (list, tuple)) and len(stoch) >= 1 else 50
        stoch_d = stoch[1] if isinstance(stoch, (list, tuple)) and len(stoch) >= 2 else 50
        
        # Fear & Greed context
        fear_greed_text = ""
        if enhanced_data.get('fear_greed_index'):
            fg = enhanced_data['fear_greed_index']
            fear_greed_text = f"\n- Fear & Greed Index: {fg['value']}/100 ({fg['classification']})"
        
        # News sentiment context
        news_text = ""
        if enhanced_data.get('news_sentiment'):
            news = enhanced_data['news_sentiment']
            news_text = f"\n- News Sentiment: {news['label']} (score: {news['score']:.2f}, {news['article_count']} articles)"
            
            # Add top headlines if available
            if news.get('top_headlines'):
                news_text += "\n- Recent Headlines:"
                for headline in news['top_headlines'][:3]:  # Top 3
                    news_text += f"\n  • {headline['title'][:80]}..." if len(headline['title']) > 80 else f"\n  • {headline['title']}"
            
            # Add news summary
            if enhanced_data.get('news_summary'):
                news_text += f"\n- News Summary: {enhanced_data['news_summary']}"
        
        # Divergence context
        divergence_text = ""
        if divergences:
            divergence_text = "\n\nDETECTED DIVERGENCES:\n"
            for div in divergences:
                divergence_text += f"- {div['type'].upper()}: {div['description']} (confidence: {div['confidence']})\n"
        
        # Pattern context
        pattern_text = ""
        if patterns:
            pattern_text = f"\n\nDETECTED PATTERNS: {', '.join(patterns)}"
        
        prompt = f"""You are an expert cryptocurrency trading analyst. Analyze the following market data for {symbol} and provide a comprehensive trading recommendation.

CURRENT MARKET DATA:
- Symbol: {symbol}
- Current Price: ${current_price:.2f}

TECHNICAL INDICATORS:
- RSI (14): {rsi:.2f}
- MACD Line: {macd_line:.2f}, Signal: {macd_signal:.2f}, Histogram: {macd_line - macd_signal:.2f}
- ADX (Trend Strength): {adx:.2f}
- Stochastic K: {stoch_k:.2f}, D: {stoch_d:.2f}
- OBV (On-Balance Volume): {obv:.0f}
- Bollinger Bands: Upper: ${bb_upper:.2f}, Middle: ${bb_middle:.2f}, Lower: ${bb_lower:.2f}
- ATR: {indicators.get('atr', 0):.2f}
- MFI (Money Flow Index): {indicators.get('mfi', 50):.2f}

ADVANCED ANALYSIS:
- Volatility Ratio: {advanced_indicators['volatility_ratio']:.3f}
- Trend Strength Score: {advanced_indicators['trend_strength']:.2f}
- Volume Profile: {advanced_indicators['volume_profile']}

MARKET SENTIMENT:{fear_greed_text}{news_text}{divergence_text}{pattern_text}

Please provide a detailed analysis in JSON format with the following structure:
{{
    "trend": "BULLISH" | "BEARISH" | "NEUTRAL",
    "recommended_action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of your analysis",
    "support_levels": [price1, price2, price3],
    "resistance_levels": [price1, price2, price3],
    "stop_loss_suggestion": price or null,
    "take_profit_suggestion": price or null,
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "key_patterns": ["pattern1", "pattern2"],
    "warnings": ["warning1", "warning2"],
    "macro_trend": "Description of longer-term outlook"
}}

Focus on:
1. Identifying the primary trend direction and strength
2. Key support/resistance levels based on Bollinger Bands and price action
3. Risk assessment considering volatility and market sentiment
4. Specific entry/exit recommendations with rationale
5. Potential risks and warnings for traders

Provide your analysis as valid JSON only, no additional text."""

        return prompt
    
    async def _call_anthropic_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Anthropic Claude API"""
        if not self.anthropic_api_key:
            logger.debug("Anthropic API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            headers = {
                'x-api-key': self.anthropic_api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            }
            
            payload = {
                'model': self.primary_model,
                'max_tokens': 2048,
                'temperature': 0.3,  # Lower temperature for more consistent analysis
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }
            
            async with session.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract text content from Claude's response
                    content = data.get('content', [])
                    if content and len(content) > 0:
                        text = content[0].get('text', '')
                        
                        # Parse JSON response
                        result = self._parse_ai_response(text)
                        if result:
                            result['model_used'] = self.primary_model
                            logger.info(f"Successfully got analysis from Claude ({self.primary_model})")
                            return result
                    
                    logger.warning("Claude API returned empty content")
                else:
                    error_text = await response.text()
                    logger.warning(f"Claude API error {response.status}: {error_text}")
        
        except Exception as e:
            logger.warning(f"Error calling Anthropic API: {e}")
        
        return None
    
    async def _call_openrouter_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenRouter API as fallback"""
        if not self.openrouter_api_key:
            logger.debug("OpenRouter API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            headers = {
                'Authorization': f'Bearer {self.openrouter_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/gpscal/trading_llm_bot',
                'X-Title': 'TradingBot Deep Analyzer'
            }
            
            payload = {
                'model': self.fallback_model,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 2048
            }
            
            async with session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract message content
                    choices = data.get('choices', [])
                    if choices and len(choices) > 0:
                        message = choices[0].get('message', {})
                        text = message.get('content', '')
                        
                        # Parse JSON response
                        result = self._parse_ai_response(text)
                        if result:
                            result['model_used'] = self.fallback_model
                            logger.info(f"Successfully got analysis from OpenRouter ({self.fallback_model})")
                            return result
                    
                    logger.warning("OpenRouter API returned empty content")
                else:
                    error_text = await response.text()
                    logger.warning(f"OpenRouter API error {response.status}: {error_text}")
        
        except Exception as e:
            logger.warning(f"Error calling OpenRouter API: {e}")
        
        return None
    
    def _parse_ai_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response text as JSON"""
        try:
            # Try to extract JSON from response (may have markdown formatting)
            text = text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```'):
                lines = text.split('\n')
                # Remove first and last lines (```json and ```)
                text = '\n'.join(lines[1:-1])
            
            # Parse JSON
            result = json.loads(text)
            
            # Validate required fields
            required_fields = ['trend', 'recommended_action', 'confidence', 'reasoning']
            if not all(field in result for field in required_fields):
                logger.warning(f"AI response missing required fields: {result.keys()}")
                return None
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _build_fallback_analysis(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Build minimal analysis when AI providers fail"""
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', (0, 0))
        macd_hist = macd[0] - macd[1] if isinstance(macd, (list, tuple)) and len(macd) >= 2 else 0
        
        # Simple heuristic-based analysis
        if rsi < 30 and macd_hist < 0:
            trend = "BEARISH"
            action = "HOLD"  # Oversold but bearish
            confidence = 0.5
        elif rsi > 70 and macd_hist > 0:
            trend = "BULLISH"
            action = "HOLD"  # Overbought but bullish
            confidence = 0.5
        elif rsi < 40:
            trend = "BEARISH"
            action = "SELL"
            confidence = 0.6
        elif rsi > 60:
            trend = "BULLISH"
            action = "BUY"
            confidence = 0.6
        else:
            trend = "NEUTRAL"
            action = "HOLD"
            confidence = 0.4
        
        return {
            'trend': trend,
            'recommended_action': action,
            'confidence': confidence,
            'reasoning': 'Fallback analysis based on RSI and MACD indicators only (AI providers unavailable)',
            'support_levels': [],
            'resistance_levels': [],
            'stop_loss_suggestion': None,
            'take_profit_suggestion': None,
            'risk_level': 'MEDIUM',
            'key_patterns': [],
            'warnings': ['Limited analysis - AI providers unavailable'],
            'macro_trend': 'Unknown - using basic indicator analysis',
            'model_used': 'fallback_heuristic'
        }
    
    def _build_analysis_result(
        self,
        symbol: str,
        current_price: float,
        indicators: Dict[str, Any],
        advanced_indicators: Dict[str, Any],
        divergences: List[Dict[str, Any]],
        patterns: List[str],
        enhanced_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        duration: float
    ) -> DeepAnalysisResult:
        """Build structured analysis result"""
        
        # Extract sentiment
        sentiment_score = None
        if enhanced_data.get('fear_greed_index'):
            sentiment_score = enhanced_data['fear_greed_index']['value'] / 100.0
        
        # Build result
        result = DeepAnalysisResult(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            timeframe='multi',  # We analyze multiple timeframes
            
            trend=ai_analysis.get('trend', 'NEUTRAL'),
            recommended_action=ai_analysis.get('recommended_action', 'HOLD'),
            confidence=float(ai_analysis.get('confidence', 0.5)),
            
            support_levels=ai_analysis.get('support_levels', []),
            resistance_levels=ai_analysis.get('resistance_levels', []),
            key_indicators={
                'rsi': indicators.get('rsi'),
                'macd': indicators.get('macd'),
                'adx': indicators.get('adx'),
                'obv': indicators.get('obv'),
                **advanced_indicators
            },
            divergences=divergences,
            
            sentiment_score=sentiment_score,
            news_summary=enhanced_data.get('news_summary'),
            news_sentiment=enhanced_data.get('news_sentiment'),
            macro_trend=ai_analysis.get('macro_trend', 'Unknown'),
            
            risk_level=ai_analysis.get('risk_level', 'MEDIUM'),
            stop_loss_suggestion=ai_analysis.get('stop_loss_suggestion'),
            take_profit_suggestion=ai_analysis.get('take_profit_suggestion'),
            
            reasoning=ai_analysis.get('reasoning', 'No reasoning provided'),
            key_patterns=ai_analysis.get('key_patterns', patterns),
            warnings=ai_analysis.get('warnings', []),
            
            analysis_duration=duration,
            ai_model_used=ai_analysis.get('model_used', 'unknown')
        )
        
        return result


# Global instance
_deep_analyzer_instance: Optional[DeepAnalyzer] = None


def get_deep_analyzer(config: Optional[Dict[str, Any]] = None) -> Optional[DeepAnalyzer]:
    """Get or create DeepAnalyzer instance"""
    global _deep_analyzer_instance
    
    if config is None:
        from config.config import CONFIG
        config = CONFIG
    
    if _deep_analyzer_instance is None:
        _deep_analyzer_instance = DeepAnalyzer(config)
    
    return _deep_analyzer_instance

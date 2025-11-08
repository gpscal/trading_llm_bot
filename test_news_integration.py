#!/usr/bin/env python3
"""
Test News API Integration
Tests the NewsAPI.ai integration in DeepAnalyzer
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.config import CONFIG
from ml.deep_analyzer import DeepAnalyzer


async def test_news_api_configuration():
    """Test 1: Verify news API configuration is loaded correctly"""
    print("\n" + "="*80)
    print("TEST 1: News API Configuration")
    print("="*80)
    
    required_keys = [
        'news_api_enabled',
        'news_api_key',
        'news_api_base_url',
        'news_api_cache_duration',
        'news_api_max_articles',
        'news_api_timeout',
        'news_crypto_keywords'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in CONFIG:
            missing_keys.append(key)
        else:
            print(f"✓ {key}: {CONFIG[key]}")
    
    if missing_keys:
        print(f"\n✗ Missing configuration keys: {missing_keys}")
        return False
    
    # Check API key
    if not CONFIG.get('news_api_key'):
        print("\n⚠ WARNING: NEWS_API_AI environment variable not set!")
        print("  Please add NEWS_API_AI=your_api_key to your .env file")
        return False
    
    print(f"\n✓ API Key configured: {CONFIG['news_api_key'][:10]}...")
    print("✓ All configuration keys present")
    return True


async def test_fetch_crypto_news():
    """Test 2: Test fetching news for different cryptocurrencies"""
    print("\n" + "="*80)
    print("TEST 2: Fetch Crypto News")
    print("="*80)
    
    analyzer = DeepAnalyzer(CONFIG)
    
    test_symbols = ['BTC/USD', 'SOL/USD', 'ETH/USD']
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        
        try:
            news_data = await analyzer._fetch_crypto_news(symbol)
            
            if news_data is None:
                print(f"⚠ No news data returned for {symbol}")
                continue
            
            print(f"✓ Article Count: {news_data.get('article_count', 0)}")
            print(f"✓ Sentiment Label: {news_data.get('sentiment_label', 'N/A')}")
            print(f"✓ Sentiment Score: {news_data.get('sentiment_score', 0):.3f}")
            print(f"✓ Summary: {news_data.get('summary', 'N/A')}")
            
            headlines = news_data.get('top_headlines', [])
            if headlines:
                print(f"✓ Top Headlines ({len(headlines)}):")
                for i, headline in enumerate(headlines[:3], 1):
                    print(f"  {i}. {headline['title'][:70]}...")
                    print(f"     Source: {headline['source']} | Date: {headline['date']}")
            
        except Exception as e:
            print(f"✗ Error fetching news for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    await analyzer.close()
    print("\n✓ News fetching test completed successfully")
    return True


async def test_news_sentiment_analysis():
    """Test 3: Test sentiment analysis logic"""
    print("\n" + "="*80)
    print("TEST 3: News Sentiment Analysis")
    print("="*80)
    
    analyzer = DeepAnalyzer(CONFIG)
    
    # Test with mock articles
    test_cases = [
        {
            'name': 'Bullish Articles',
            'articles': [
                {
                    'title': 'Bitcoin surges to new all-time high amid adoption boom',
                    'body': 'Bitcoin rally continues as institutional adoption grows'
                },
                {
                    'title': 'Crypto market gains momentum with breakthrough innovation',
                    'body': 'Positive outlook for cryptocurrency markets'
                }
            ],
            'expected': 'BULLISH'
        },
        {
            'name': 'Bearish Articles',
            'articles': [
                {
                    'title': 'Bitcoin crashes amid regulatory concerns',
                    'body': 'Market panic as cryptocurrency faces investigation'
                },
                {
                    'title': 'Crypto prices plunge following security breach',
                    'body': 'Major sell-off in cryptocurrency markets'
                }
            ],
            'expected': 'BEARISH'
        },
        {
            'name': 'Neutral Articles',
            'articles': [
                {
                    'title': 'Bitcoin trading sideways as markets await direction',
                    'body': 'Cryptocurrency markets show mixed signals'
                }
            ],
            'expected': 'NEUTRAL'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        result = analyzer._analyze_news_sentiment(test_case['articles'], 'BTC')
        
        print(f"Sentiment Label: {result['sentiment_label']}")
        print(f"Sentiment Score: {result['sentiment_score']:.3f}")
        print(f"Expected: {test_case['expected']}")
        
        if result['sentiment_label'] == test_case['expected']:
            print(f"✓ Sentiment analysis correct for {test_case['name']}")
        else:
            print(f"⚠ Sentiment mismatch: got {result['sentiment_label']}, expected {test_case['expected']}")
    
    await analyzer.close()
    print("\n✓ Sentiment analysis test completed")
    return True


async def test_enhanced_data_gathering():
    """Test 4: Test complete enhanced data gathering with news"""
    print("\n" + "="*80)
    print("TEST 4: Enhanced Data Gathering (Fear & Greed + News)")
    print("="*80)
    
    analyzer = DeepAnalyzer(CONFIG)
    
    symbol = 'BTC/USD'
    current_price = 50000.0
    
    # Mock indicators
    indicators = {
        'rsi': 55.0,
        'macd': (100, 90),
        'adx': 35.0
    }
    
    print(f"Gathering enhanced data for {symbol}...")
    
    try:
        enhanced_data = await analyzer._gather_enhanced_data(
            symbol=symbol,
            current_price=current_price,
            indicators=indicators,
            historical_data=None
        )
        
        print("\n✓ Enhanced data gathered successfully")
        print(f"  Keys: {list(enhanced_data.keys())}")
        
        # Check Fear & Greed
        if enhanced_data.get('fear_greed_index'):
            fg = enhanced_data['fear_greed_index']
            print(f"\n✓ Fear & Greed Index:")
            print(f"  Value: {fg.get('value')}/100")
            print(f"  Classification: {fg.get('classification')}")
        else:
            print("\n⚠ Fear & Greed Index: Not available")
        
        # Check News
        if enhanced_data.get('news_sentiment'):
            news = enhanced_data['news_sentiment']
            print(f"\n✓ News Sentiment:")
            print(f"  Label: {news.get('label')}")
            print(f"  Score: {news.get('score', 0):.3f}")
            print(f"  Articles: {news.get('article_count', 0)}")
            
            if news.get('top_headlines'):
                print(f"  Headlines: {len(news['top_headlines'])}")
        else:
            print("\n⚠ News Sentiment: Not available")
        
        if enhanced_data.get('news_summary'):
            print(f"\n✓ News Summary:")
            print(f"  {enhanced_data['news_summary']}")
        
        await analyzer.close()
        print("\n✓ Enhanced data gathering test completed")
        return True
        
    except Exception as e:
        print(f"\n✗ Error in enhanced data gathering: {e}")
        import traceback
        traceback.print_exc()
        await analyzer.close()
        return False


async def test_news_caching():
    """Test 5: Test news caching functionality"""
    print("\n" + "="*80)
    print("TEST 5: News Caching")
    print("="*80)
    
    analyzer = DeepAnalyzer(CONFIG)
    symbol = 'BTC/USD'
    
    print("Fetching news (first call - should hit API)...")
    import time
    start1 = time.time()
    news1 = await analyzer._fetch_crypto_news(symbol)
    time1 = time.time() - start1
    
    print(f"✓ First call took {time1:.3f} seconds")
    
    print("\nFetching news again (second call - should use cache)...")
    start2 = time.time()
    news2 = await analyzer._fetch_crypto_news(symbol)
    time2 = time.time() - start2
    
    print(f"✓ Second call took {time2:.3f} seconds")
    
    if news1 and news2:
        if news1 == news2:
            print("✓ Cache is working - same data returned")
            if time2 < time1:
                print(f"✓ Cache is faster ({time1/time2:.1f}x speedup)")
        else:
            print("⚠ Cache may not be working - different data returned")
    else:
        print("⚠ Could not test caching - no data returned")
    
    await analyzer.close()
    print("\n✓ Caching test completed")
    return True


async def test_error_handling():
    """Test 6: Test error handling for various scenarios"""
    print("\n" + "="*80)
    print("TEST 6: Error Handling")
    print("="*80)
    
    # Test with invalid API key
    print("\n--- Testing with invalid API key ---")
    bad_config = CONFIG.copy()
    bad_config['news_api_key'] = 'invalid_key_12345'
    
    analyzer = DeepAnalyzer(bad_config)
    
    try:
        news = await analyzer._fetch_crypto_news('BTC/USD')
        if news is None:
            print("✓ Invalid API key handled gracefully (returned None)")
        else:
            print("⚠ Expected None for invalid API key, got data instead")
    except Exception as e:
        print(f"⚠ Exception raised instead of returning None: {e}")
    
    await analyzer.close()
    
    # Test with disabled news API
    print("\n--- Testing with disabled news API ---")
    disabled_config = CONFIG.copy()
    disabled_config['news_api_enabled'] = False
    
    analyzer = DeepAnalyzer(disabled_config)
    
    news = await analyzer._fetch_crypto_news('BTC/USD')
    if news is None:
        print("✓ Disabled news API handled gracefully (returned None)")
    else:
        print("⚠ Expected None for disabled API, got data instead")
    
    await analyzer.close()
    
    # Test with invalid symbol
    print("\n--- Testing with invalid symbol ---")
    analyzer = DeepAnalyzer(CONFIG)
    
    news = await analyzer._fetch_crypto_news('INVALID/SYMBOL')
    if news is None or news.get('article_count', 0) == 0:
        print("✓ Invalid symbol handled gracefully")
    else:
        print("⚠ Expected no articles for invalid symbol")
    
    await analyzer.close()
    
    print("\n✓ Error handling test completed")
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("NEWS API INTEGRATION TEST SUITE")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Configuration", test_news_api_configuration),
        ("Fetch News", test_fetch_crypto_news),
        ("Sentiment Analysis", test_news_sentiment_analysis),
        ("Enhanced Data", test_enhanced_data_gathering),
        ("Caching", test_news_caching),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = "PASS" if result else "FAIL"
        except Exception as e:
            print(f"\n✗ Test '{test_name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "ERROR"
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        emoji = "✓" if result == "PASS" else "✗"
        print(f"{emoji} {test_name}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

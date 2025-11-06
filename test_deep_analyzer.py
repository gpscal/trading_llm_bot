#!/usr/bin/env python3
"""
Test script for Deep Analyzer integration
"""
import asyncio
import sys
from config.config import CONFIG
from ml.deep_analyzer import get_deep_analyzer

async def test_deep_analyzer():
    """Test deep analyzer initialization and analysis generation"""
    print("=" * 80)
    print("Testing Deep Analyzer Integration (Claude AI + RAG)")
    print("=" * 80)
    
    # Check configuration
    print("\n1. Checking configuration...")
    deep_enabled = CONFIG.get('deep_analysis_enabled', False)
    anthropic_key = CONFIG.get('anthropic_api_key')
    openrouter_key = CONFIG.get('openrouter_api_key')
    
    print(f"   ? Deep Analysis Enabled: {deep_enabled}")
    print(f"   ? Anthropic API Key: {'SET' if anthropic_key else 'NOT SET'}")
    print(f"   ? OpenRouter API Key: {'SET' if openrouter_key else 'NOT SET'}")
    print(f"   ? Analysis Interval: {CONFIG.get('deep_analysis_interval', 7200)}s")
    print(f"   ? Primary Model: {CONFIG.get('deep_analysis_model', 'claude-3-5-sonnet-20241022')}")
    
    if not anthropic_key:
        print("\n??  WARNING: ANTHROPIC_API_KEY not set in .env file")
        print("   Please add your Anthropic API key to .env:")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        print("\n   Get your key from: https://console.anthropic.com/")
        return False
    
    print("\n2. Getting Deep Analyzer instance...")
    try:
        analyzer = get_deep_analyzer(CONFIG)
        print(f"   ? Analyzer created")
        print(f"   - Enabled: {analyzer.enabled}")
    except Exception as e:
        print(f"   ? Error creating analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if not analyzer.enabled:
        print("\n   ??  Deep Analysis is disabled in config")
        print("   Set 'deep_analysis_enabled': True in config.py")
        return False
    
    print("\n3. Testing Fear & Greed Index fetch...")
    try:
        fear_greed = await analyzer._fetch_fear_greed_index()
        if fear_greed:
            print(f"   ? Fear & Greed Index: {fear_greed['value']}/100 ({fear_greed['classification']})")
        else:
            print(f"   ??  Could not fetch Fear & Greed Index (API may be down)")
    except Exception as e:
        print(f"   ??  Error fetching Fear & Greed: {e}")
    
    print("\n4. Testing Deep Analysis (this may take 10-30 seconds)...")
    print("   Analyzing BTC market with Claude AI...")
    
    try:
        # Create mock indicators for BTC
        btc_indicators = {
            'rsi': 52.3,
            'macd': (250.5, 180.2),
            'adx': 28.5,
            'obv': 125000.0,
            'bollinger_bands': (68000, 66500, 65000),
            'stochastic_oscillator': (55, 52),
            'atr': 1200.0,
            'mfi': 58.0,
            'vwap': 66800.0,
        }
        
        analysis = await analyzer.get_analysis(
            symbol='BTC/USD',
            current_price=66500.0,
            indicators=btc_indicators,
            historical_data=None,
            force_refresh=True  # Force new analysis for testing
        )
        
        if analysis:
            print(f"\n   ? Analysis received!")
            print(f"\n   ?? ANALYSIS RESULTS:")
            print(f"   {'='*70}")
            print(f"   Symbol: {analysis.symbol}")
            print(f"   Trend: {analysis.trend}")
            print(f"   Recommendation: {analysis.recommended_action}")
            print(f"   Confidence: {analysis.confidence:.1%}")
            print(f"   Risk Level: {analysis.risk_level}")
            print(f"   Sentiment: {analysis.sentiment_score:.1%}" if analysis.sentiment_score else "   Sentiment: N/A")
            print(f"   AI Model: {analysis.ai_model_used}")
            print(f"   Duration: {analysis.analysis_duration:.2f}s")
            
            if analysis.support_levels:
                print(f"\n   Support Levels: {', '.join([f'${x:.2f}' for x in analysis.support_levels])}")
            if analysis.resistance_levels:
                print(f"   Resistance Levels: {', '.join([f'${x:.2f}' for x in analysis.resistance_levels])}")
            
            if analysis.stop_loss_suggestion:
                print(f"\n   Stop Loss: ${analysis.stop_loss_suggestion:.2f}")
            if analysis.take_profit_suggestion:
                print(f"   Take Profit: ${analysis.take_profit_suggestion:.2f}")
            
            print(f"\n   ?? REASONING:")
            print(f"   {'-'*70}")
            # Print reasoning with line wrapping
            reasoning_lines = analysis.reasoning.split('. ')
            for line in reasoning_lines:
                if line.strip():
                    print(f"   {line.strip()}.")
            
            if analysis.key_patterns:
                print(f"\n   ?? KEY PATTERNS:")
                for pattern in analysis.key_patterns:
                    print(f"   - {pattern}")
            
            if analysis.warnings:
                print(f"\n   ??  WARNINGS:")
                for warning in analysis.warnings:
                    print(f"   - {warning}")
            
            if analysis.divergences:
                print(f"\n   ?? DIVERGENCES DETECTED:")
                for div in analysis.divergences:
                    print(f"   - {div.get('type', 'N/A').upper()}: {div.get('description', 'N/A')}")
            
            print(f"\n   {'='*70}")
            print("\n   ? Deep Analyzer is working correctly!")
            
            # Test caching
            print("\n5. Testing cache (should return instantly)...")
            cached_analysis = await analyzer.get_analysis(
                symbol='BTC/USD',
                current_price=66500.0,
                indicators=btc_indicators,
                historical_data=None,
                force_refresh=False  # Use cache
            )
            
            if cached_analysis and cached_analysis.timestamp == analysis.timestamp:
                print(f"   ? Cache is working! Analysis returned instantly from cache.")
            else:
                print(f"   ??  Cache may not be working properly")
            
            return True
        else:
            print(f"   ? No analysis received (check deep_analyzer.log for details)")
            print(f"   - This may be due to API issues or rate limiting")
            return False
            
    except Exception as e:
        print(f"   ? Error getting analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        await analyzer.close()

def main():
    """Main test function"""
    try:
        result = asyncio.run(test_deep_analyzer())
        if result:
            print("\n" + "=" * 80)
            print("? All tests passed! Deep Analyzer is ready to use.")
            print("=" * 80)
            print("\nNext steps:")
            print("1. Ensure ANTHROPIC_API_KEY is set in .env file")
            print("2. Deep analysis is already enabled in config.py")
            print("3. Start your simulation - deep analysis will run every 2 hours")
            print("4. Monitor deep_analyzer.log for detailed analysis logs")
            print("\nNote: Deep analysis complements your fast LLM advisor:")
            print("- Fast LLM: Every 60s for quick signals (local DeepSeek)")
            print("- Deep Analysis: Every 2 hours for comprehensive context (Claude AI)")
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("? Tests failed. Check errors above.")
            print("=" * 80)
            print("\nTroubleshooting:")
            print("1. Make sure ANTHROPIC_API_KEY is set in .env")
            print("2. Check your internet connection")
            print("3. Review deep_analyzer.log for error details")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

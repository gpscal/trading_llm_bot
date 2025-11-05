#!/usr/bin/env python3
"""
Test script for LLM Advisor integration
"""
import asyncio
import sys
from config.config import CONFIG
from ml.llm_advisor import get_llm_advisor

async def test_llm_advisor():
    """Test LLM advisor initialization and signal generation"""
    print("=" * 60)
    print("Testing LLM Advisor Integration")
    print("=" * 60)
    
    # Enable LLM for testing
    CONFIG['llm_enabled'] = True
    
    print("\n1. Getting LLM advisor instance...")
    try:
        advisor = get_llm_advisor(CONFIG)
        print(f"   ? Advisor created")
        print(f"   - Enabled: {advisor.enabled}")
        print(f"   - Initialized: {advisor._initialized}")
    except Exception as e:
        print(f"   ? Error creating advisor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if not advisor.enabled:
        print("\n   ? LLM is disabled in config. Enabling for test...")
        CONFIG['llm_enabled'] = True
        advisor = get_llm_advisor(CONFIG)
    
    if not advisor._initialized:
        print("\n2. Initializing LLM components...")
        try:
            advisor._initialize_llm()
            if advisor._initialized:
                print(f"   ? LLM initialized successfully")
            else:
                print(f"   ? Failed to initialize (check config file)")
                return False
        except Exception as e:
            print(f"   ? Initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n3. Testing LLM signal generation...")
    print("   Generating trading signal (this may take 5-10 seconds)...")
    
    try:
        # Create mock indicators
        btc_indicators = {
            'rsi': 45.5,
            'macd': [-50.2, 50.8],
            'momentum': 150.3,
            'adx': 25.0,
            'obv': 12345.67,
            'bollinger_bands': (66000, 65000, 64000),
            'stochastic_oscillator': (45, 50)
        }
        
        sol_indicators = {
            'rsi': 50.2,
            'macd': [-0.5, 0.8],
            'adx': 22.0,
            'obv': 5678.90,
            'bollinger_bands': (185, 184, 183),
            'stochastic_oscillator': (48, 52)
        }
        
        signal = await advisor.get_trading_signal(
            sol_price=184.25,
            btc_price=65000.0,
            btc_indicators=btc_indicators,
            sol_indicators=sol_indicators,
            balance_usdt=1000.0,
            balance_sol=0.0,
            sol_historical=None,  # Optional
            btc_historical=None  # Optional
        )
        
        if signal:
            print(f"   ? Signal received!")
            print(f"\n   Signal Details:")
            print(f"   - Signal: {signal.get('signal', 'N/A')}")
            print(f"   - Confidence: {signal.get('confidence', 'N/A')}")
            print(f"   - Confidence Score: {signal.get('confidence_score', 0):.2f}")
            print(f"   - Stop Loss: {signal.get('stop_loss', 'N/A')}")
            print(f"   - Take Profit: {signal.get('take_profit', 'N/A')}")
            print(f"   - Reasoning: {signal.get('reasoning', 'N/A')[:200]}...")
            print("\n   ? LLM Advisor is working correctly!")
            return True
        else:
            print(f"   ? No signal received (may be throttled or model issue)")
            print(f"   - Check llm_advisor.log for details")
            return False
            
    except Exception as e:
        print(f"   ? Error getting signal: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    try:
        result = asyncio.run(test_llm_advisor())
        if result:
            print("\n" + "=" * 60)
            print("? All tests passed! LLM Advisor is ready to use.")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Enable LLM in config.py: 'llm_enabled': True")
            print("2. Start your simulation")
            print("3. Monitor llm_advisor.log for LLM signals")
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("? Tests failed. Check errors above.")
            print("=" * 60)
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

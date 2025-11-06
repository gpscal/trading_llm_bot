#!/usr/bin/env python3
"""
Test script to verify Deep Analyzer model configuration from .env
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.config import CONFIG
from ml.deep_analyzer import get_deep_analyzer

def test_model_config():
    """Test that Deep Analyzer uses the correct model from .env"""
    print("=" * 70)
    print("Deep Analyzer Model Configuration Test")
    print("=" * 70)
    
    # Check .env file
    print("\n1. Environment Variable:")
    anthropic_model = os.getenv('ANTHROPIC_MODEL')
    print(f"   ANTHROPIC_MODEL = {anthropic_model}")
    
    # Check CONFIG
    print("\n2. CONFIG Dictionary:")
    config_model = CONFIG.get('deep_analysis_model')
    anthropic_model_config = CONFIG.get('anthropic_model')
    print(f"   deep_analysis_model = {config_model}")
    print(f"   anthropic_model = {anthropic_model_config}")
    
    # Check Deep Analyzer instance
    print("\n3. Deep Analyzer Instance:")
    try:
        analyzer = get_deep_analyzer(CONFIG)
        print(f"   Enabled: {analyzer.enabled}")
        print(f"   Primary Model: {analyzer.primary_model}")
        print(f"   Fallback Model: {analyzer.fallback_model}")
        print(f"   Analysis Interval: {analyzer.analysis_interval}s ({analyzer.analysis_interval/3600:.1f} hours)")
        
        # Verify model matches .env
        print("\n4. Verification:")
        if analyzer.primary_model == anthropic_model:
            print(f"   ✅ SUCCESS: Deep Analyzer is using {anthropic_model} from .env")
        else:
            print(f"   ❌ MISMATCH: Expected {anthropic_model}, but got {analyzer.primary_model}")
            return False
        
        # Check API key (without revealing it)
        if analyzer.anthropic_api_key:
            print(f"   ✅ Anthropic API key is configured (length: {len(analyzer.anthropic_api_key)})")
        else:
            print(f"   ⚠️  WARNING: Anthropic API key not found")
        
        print("\n" + "=" * 70)
        print("✅ Configuration test PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_model_config()
    sys.exit(0 if success else 1)

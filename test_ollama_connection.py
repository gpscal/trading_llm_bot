#!/usr/bin/env python3
"""Quick test to verify Ollama is running and DeepSeek-R1:8b model is accessible"""
import requests
import json
import sys

def test_ollama():
    """Test Ollama connection and model availability"""
    print("=" * 50)
    print("Ollama Connection Test")
    print("=" * 50)
    
    try:
        # Test Ollama API
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running!")
            print(f"\nAvailable models:")
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0) / (1024**3)  # Convert to GB
                print(f"  - {name} ({size:.1f} GB)")
            
            # Check if deepseek-r1:8b is available
            deepseek_models = [m for m in models if 'deepseek-r1:8b' in m.get('name', '').lower()]
            if deepseek_models:
                print(f"\n✅ DeepSeek-R1:8b model found!")
                for m in deepseek_models:
                    print(f"   Model: {m.get('name')}")
            else:
                # Check for other deepseek models
                other_deepseek = [m for m in models if 'deepseek' in m.get('name', '').lower()]
                if other_deepseek:
                    print(f"\n⚠️  DeepSeek-R1:8b not found, but found other DeepSeek models:")
                    for m in other_deepseek:
                        print(f"   - {m.get('name')}")
                    print(f"\n   To install deepseek-r1:8b, run: ollama pull deepseek-r1:8b")
                else:
                    print(f"\n❌ No DeepSeek models found!")
                    print(f"   Install with: ollama pull deepseek-r1:8b")
                    return False
            
            # Test model with a simple prompt
            print("\n" + "-" * 50)
            print("Testing model with simple prompt...")
            print("-" * 50)
            
            test_response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    "model": "deepseek-r1:8b",
                    "prompt": "Say 'Hello, trading bot!' in exactly those words.",
                    "stream": False,
                    "options": {"num_predict": 50}
                },
                timeout=120  # 2 minute timeout
            )
            
            if test_response.status_code == 200:
                result = test_response.json().get('response', '')
                print(f"✅ Model response: {result[:100]}...")
                print("\n✅ Ollama and DeepSeek-R1:8b are ready for trading analysis!")
                return True
            else:
                print(f"❌ Model test failed: {test_response.status_code}")
                print(f"   Response: {test_response.text[:200]}")
                return False
                
        else:
            print(f"❌ Ollama API returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running?")
        print("   Start it with: ollama serve")
        print("   Or check if it's running: systemctl status ollama")
        return False
    except requests.exceptions.Timeout:
        print("❌ Ollama request timed out. The model might be loading...")
        print("   Try again in a moment, or check system resources.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Quick test to verify Ollama is running and model is accessible"""
import requests
import json

try:
    # Test Ollama API
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"? Ollama is running!")
        print(f"\nAvailable models:")
        for model in models:
            print(f"  - {model.get('name', 'Unknown')}")
        
        # Check if deepseek-r1 is available
        deepseek_models = [m for m in models if 'deepseek' in m.get('name', '').lower()]
        if deepseek_models:
            print(f"\n? DeepSeek-R1 model found:")
            for m in deepseek_models:
                print(f"  - {m.get('name')}")
        else:
            print(f"\n??  DeepSeek-R1 model not found in list")
            print(f"   Make sure you ran: ollama pull deepseek-r1:1.5b")
    else:
        print(f"? Ollama API returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("? Cannot connect to Ollama. Is it running?")
    print("   Start it with: ollama serve")
except Exception as e:
    print(f"? Error: {e}")

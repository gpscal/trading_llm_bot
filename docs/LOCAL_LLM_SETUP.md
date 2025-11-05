# Local LLM Setup for RTX 3050 Mobile

## GPU Specifications

**NVIDIA RTX 3050 Mobile:**
- **VRAM**: 4GB GDDR6
- **CUDA Cores**: ~2048
- **Recommended**: 3B-7B quantized models
- **Best Performance**: Q4_K_M or Q5_K_M quantization

## Recommended Models (Ranked)

### 1. **DeepSeek-R1 1.5B** (? Best for Trading)
- **Size**: ~1.5GB (Q4_K_M)
- **Why**: Chain-of-thought reasoning model, perfect for trading analysis
- **Speed**: Very fast on 4GB VRAM
- **Quality**: Excellent reasoning capabilities
- **Download**: [HuggingFace](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-3-70B) (look for 1.5B variant)
- **LM Studio ID**: `deepseek-r1-distill-1.5b-q4_k_m` (if available)

### 2. **Phi-3 Mini 3.8B** (? Excellent Reasoning)
- **Size**: ~2.4GB (Q4_K_M), ~3.0GB (Q5_K_M)
- **Why**: Microsoft's efficient reasoning model
- **Speed**: Fast inference
- **Quality**: Great for structured analysis
- **Download**: `microsoft/Phi-3-mini-4k-instruct`

### 3. **Qwen2.5 3B** (Balanced)
- **Size**: ~2.0GB (Q4_K_M), ~2.5GB (Q5_K_M)
- **Why**: Strong general capabilities, good reasoning
- **Speed**: Fast
- **Quality**: Well-rounded for various tasks
- **Download**: `Qwen/Qwen2.5-3B-Instruct`

### 4. **Llama 3.2 3B** (General Purpose)
- **Size**: ~2.0GB (Q4_K_M), ~2.5GB (Q5_K_M)
- **Why**: Meta's efficient model, good for structured tasks
- **Speed**: Fast
- **Quality**: Reliable performance
- **Download**: `meta-llama/Llama-3.2-3B-Instruct`

### 5. **Mistral 7B Q4_K_M** (If you want larger model)
- **Size**: ~4.1GB (Q4_K_M) - **Fits tightly on 4GB**
- **Why**: More capable, but slower
- **Speed**: Slower but manageable
- **Quality**: Higher quality outputs
- **Note**: May need to reduce context size
- **Download**: `mistralai/Mistral-7B-Instruct-v0.2`

## Installation Guide

### Option A: LM Studio (Easiest - Recommended)

1. **Download LM Studio**:
   ```bash
   # Linux
   wget https://lmstudio.ai/download/latest/linux -O lm-studio.deb
   sudo dpkg -i lm-studio.deb
   
   # Or visit: https://lmstudio.ai/
   ```

2. **Open LM Studio**:
   - Go to "Search" tab
   - Search for: `Phi-3 Mini` or `DeepSeek-R1` or `Qwen2.5-3B`
   - Click "Download" ? Choose **Q4_K_M** or **Q5_K_M** quantization

3. **Start Local Server**:
   - Go to "Chat" tab ? Click "Start Server" button
   - Server runs on `http://localhost:1234/v1`
   - This is already configured in your `model_config.ini.template`!

4. **Update Config**:
   Edit `LLM_trader/config/model_config.ini`:
   ```ini
   [model]
   name = Phi-3-Mini-3.8B-Instruct  # Name from LM Studio
   base_url = http://localhost:1234/v1
   api_key = lm-studio
   ```

### Option B: Ollama (Alternative)

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull Model**:
   ```bash
   # Recommended models for 4GB VRAM
   ollama pull phi3:3.8b-mini
   ollama pull qwen2.5:3b
   ollama pull llama3.2:3b
   ```

3. **Start Server**:
   ```bash
   ollama serve
   ```

4. **Update Config**:
   ```ini
   [model]
   name = phi3:3.8b-mini
   base_url = http://localhost:11434/v1
   api_key = ollama
   ```

### Option C: vLLM (Fastest, Advanced)

For production use with better performance:

```bash
pip install vllm

# Run server
python -m vllm.entrypoints.openai.api_server \
    --model microsoft/Phi-3-mini-4k-instruct \
    --tensor-parallel-size 1 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.85
```

## Configuration for Your Bot

### Recommended Settings

Edit `config/config.py`:

```python
CONFIG = {
    # ... existing settings ...
    
    # LLM Trading Advisor settings
    'llm_enabled': True,
    'llm_confidence_weight': 0.20,  # Start conservative (local models may be slower)
    'llm_model_config_path': 'LLM_trader/config/model_config.ini',
}
```

### Model Config

Edit `LLM_trader/config/model_config.ini`:

```ini
[model]
# For LM Studio
name = Phi-3-Mini-3.8B-Instruct
base_url = http://localhost:1234/v1
api_key = lm-studio

# For Ollama
# name = phi3:3.8b-mini
# base_url = http://localhost:11434/v1
# api_key = ollama
```

## Performance Tips

### 1. **Reduce Context Size** (if needed)
   - Default: 4096 tokens
   - For 4GB VRAM: 2048-3072 tokens is safer
   - Edit prompt builder if needed

### 2. **Use Appropriate Quantization**
   - **Q4_K_M**: Best balance (recommended)
   - **Q5_K_M**: Better quality, slightly larger
   - **Q2_K**: Too low quality
   - **Q8_0**: Too large for 4GB

### 3. **Monitor GPU Memory**
   ```bash
   watch -n 1 nvidia-smi
   ```

### 4. **Adjust LLM Call Frequency**
   The advisor already caches (60s interval), but you can increase:
   ```python
   # In llm_advisor.py, adjust:
   _min_call_interval = 120  # 2 minutes instead of 1
   ```

## Testing Your Setup

### 1. Test Model Loading

```bash
# For LM Studio - check server is running
curl http://localhost:1234/v1/models

# For Ollama
curl http://localhost:11434/api/tags
```

### 2. Test LLM Advisor

```python
python -c "
import asyncio
from ml.llm_advisor import get_llm_advisor
from config.config import CONFIG

async def test():
    advisor = get_llm_advisor(CONFIG)
    if not advisor.enabled:
        print('Enable LLM in config first!')
        return
    
    signal = await advisor.get_trading_signal(
        sol_price=184.0,
        btc_price=65000.0,
        btc_indicators={'rsi': 45, 'macd': [-50, 50], 'momentum': 100},
        sol_indicators={'rsi': 50, 'macd': [-0.5, 0.5]},
        balance_usdt=1000.0,
        balance_sol=0.0
    )
    print(f'Signal: {signal}')

asyncio.run(test())
"
```

### 3. Check Logs

```bash
tail -f llm_advisor.log
```

## Model Comparison Table

| Model | Size (Q4_K_M) | Speed | Reasoning | Best For |
|-------|---------------|-------|-----------|----------|
| DeepSeek-R1 1.5B | ~1.5GB | ????? | ????? | Trading analysis |
| Phi-3 Mini 3.8B | ~2.4GB | ???? | ???? | General + reasoning |
| Qwen2.5 3B | ~2.0GB | ???? | ???? | Balanced |
| Llama 3.2 3B | ~2.0GB | ???? | ??? | General purpose |
| Mistral 7B | ~4.1GB | ??? | ???? | Higher quality |

## Troubleshooting

### "Out of Memory" Error

**Solution**: Use smaller model or reduce context size
- Switch to 1.5B-3B models
- Use Q4_K_M instead of Q5_K_M
- Reduce context length in prompt

### Slow Response Times

**Solution**: Optimize settings
- Use Q4_K_M quantization
- Reduce context size
- Increase cache duration (call less frequently)

### Model Not Found

**Solution**: Check model name matches exactly
- In LM Studio, note exact model name
- Use that exact name in `model_config.ini`
- Case-sensitive!

### Connection Refused

**Solution**: Start local server
```bash
# Check if server is running
curl http://localhost:1234/v1/models

# Start LM Studio server (GUI) or:
ollama serve
```

## Recommendation for Your Setup

**Best Choice**: **Phi-3 Mini 3.8B Q4_K_M** or **DeepSeek-R1 1.5B Q4_K_M**

**Why**:
- ? Fits comfortably in 4GB VRAM (~2.4GB used)
- ? Fast inference (< 2 seconds per call)
- ? Good reasoning for trading decisions
- ? Reliable and stable

**Setup Steps**:
1. Install LM Studio
2. Download "Phi-3 Mini 3.8B" with Q4_K_M quantization
3. Start server in LM Studio
4. Update `model_config.ini` with model name
5. Enable in `config.py`
6. Test and monitor!

## Performance Expectations

With RTX 3050 Mobile 4GB:

- **Response Time**: 1-5 seconds per call
- **VRAM Usage**: 2-3.5GB (leaves room for system)
- **Throughput**: ~10-20 tokens/second
- **Cache Impact**: With 60s caching, very manageable!

## Next Steps

1. ? Choose a model (recommend Phi-3 Mini or DeepSeek-R1)
2. ? Install LM Studio or Ollama
3. ? Download model with Q4_K_M quantization
4. ? Start local server
5. ? Update `model_config.ini`
6. ? Enable in `config.py`
7. ? Test with simulation
8. ? Monitor performance

Your RTX 3050 Mobile is perfectly capable of running local LLMs for trading analysis! ??

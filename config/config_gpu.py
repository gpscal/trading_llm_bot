# GPU Configuration for SolBot

# Enable/disable GPU acceleration
USE_GPU = True  # Set to False to use CPU fallback

# GPU device selection (for multi-GPU systems)
GPU_DEVICE_ID = 0

# Batch processing settings
GPU_BATCH_SIZE = 32  # Number of indicators to calculate in parallel
GPU_MAX_MEMORY_FRACTION = 0.8  # Use 80% of GPU memory

# ML Model settings
ML_MODEL_ENABLED = False  # Enable ML price prediction
ML_MODEL_TYPE = 'lstm'  # 'lstm' or 'transformer'
ML_MODEL_PATH = 'models/price_predictor.pth'  # Path to trained model
ML_SEQUENCE_LENGTH = 60  # Number of historical candles to use
ML_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to use ML prediction

# Parallel backtesting settings
BACKTEST_GPU_ENABLED = False
BACKTEST_PARALLEL_STRATEGIES = 100  # Number of strategies to test in parallel

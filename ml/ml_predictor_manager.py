"""
ML Predictor Manager - Manages ML model loading and inference.
"""

import sys
import os
# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict
from ml.price_predictor import PricePredictor, LSTMPredictor
from ml.ml_feature_extractor import MLFeatureExtractor
import logging

logger = logging.getLogger('ml_predictor_manager')


class MLPredictorManager:
    """Manages ML model for real-time predictions."""
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        Initialize ML predictor manager.
        
        Args:
            model_path: Path to trained model (default: models/price_predictor.pth)
            use_gpu: Whether to use GPU for inference
        """
        self.model_path = model_path or 'models/price_predictor.pth'
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.predictor = None
        self.feature_extractor = MLFeatureExtractor()
        self.model_loaded = False
        
    def load_model(self) -> bool:
        """Load the ML model if available."""
        if not Path(self.model_path).exists():
            logger.warning(f"ML model not found at {self.model_path}. ML predictions disabled.")
            return False
        
        try:
            # Initialize predictor (model architecture should match training)
            # We'll determine input_size dynamically or use default
            self.predictor = PricePredictor(
                model_type='lstm',
                use_gpu=self.use_gpu
            )
            
            # Load trained weights
            self.predictor.load_model(self.model_path)
            self.model_loaded = True
            logger.info(f"ML model loaded from {self.model_path} (GPU: {self.use_gpu})")
            return True
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.model_loaded = False
            return False
    
    async def predict(self, 
                     sol_historical: list,
                     btc_historical: Optional[list] = None,
                     balance: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make ML prediction for current market state.
        
        Args:
            sol_historical: Recent SOL OHLCV candles
            btc_historical: Recent BTC OHLCV candles
            balance: Current balance dict with indicators
            
        Returns:
            Dictionary with:
            - direction: 'up', 'down', or 'hold'
            - confidence: float 0-1
            - price_change_prediction: predicted price change percentage
            Or None if prediction fails
        """
        if not self.model_loaded:
            if not self.load_model():
                return None
        
        # Extract features
        features = await self.feature_extractor.extract_features_for_prediction(
            sol_historical, btc_historical, balance
        )
        
        if features is None:
            logger.warning("Failed to extract features for ML prediction")
            return None
        
        try:
            # Make prediction
            prediction = self.predictor.predict(features)
            
            # Map direction to string
            direction_probs = prediction['direction']
            direction_idx = np.argmax(direction_probs)
            direction_map = {0: 'down', 1: 'hold', 2: 'up'}
            direction = direction_map[direction_idx]
            
            # Confidence is the probability of the predicted direction
            confidence = float(direction_probs[direction_idx])
            
            return {
                'direction': direction,
                'confidence': confidence,
                'price_change_prediction': float(prediction['price']),
                'direction_probabilities': {
                    'up': float(direction_probs[2]),
                    'hold': float(direction_probs[1]),
                    'down': float(direction_probs[0])
                }
            }
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if ML model is available and loaded."""
        return self.model_loaded


# Global instance (singleton pattern)
_ml_predictor_manager = None

def get_ml_predictor_manager(model_path: Optional[str] = None, use_gpu: bool = True) -> MLPredictorManager:
    """Get or create global ML predictor manager."""
    global _ml_predictor_manager
    if _ml_predictor_manager is None:
        _ml_predictor_manager = MLPredictorManager(model_path, use_gpu)
    return _ml_predictor_manager

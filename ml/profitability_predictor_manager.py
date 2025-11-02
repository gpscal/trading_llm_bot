"""
Profitability Predictor Manager - Manages profitability prediction model.

This model predicts whether a trade will be profitable based on market conditions
at the time of entry, using data learned from historical trade outcomes.
"""

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import torch
import numpy as np
import json
from pathlib import Path
from typing import Optional, Dict, List
from ml.train_from_outcomes import ProfitabilityPredictor
from ml.data_collector import extract_features
import logging

logger = logging.getLogger('profitability_predictor_manager')


class ProfitabilityPredictorManager:
    """Manages profitability prediction model for real-time predictions."""
    
    def __init__(self, model_path: Optional[str] = None, norm_path: Optional[str] = None, use_gpu: bool = True):
        """
        Initialize profitability predictor manager.
        
        Args:
            model_path: Path to trained model (default: models/profitability_predictor.pth)
            norm_path: Path to normalization parameters (default: models/profitability_predictor_norm.json)
            use_gpu: Whether to use GPU for inference
        """
        self.model_path = model_path or 'models/profitability_predictor.pth'
        self.norm_path = norm_path or 'models/profitability_predictor_norm.json'
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_gpu else 'cpu')
        self.model = None
        self.norm_mean = None
        self.norm_std = None
        self.model_loaded = False
        self.input_size = 20  # Default, will be inferred from model
        self.sequence_length = 60
        
    def load_model(self) -> bool:
        """Load the profitability prediction model if available."""
        if not Path(self.model_path).exists():
            logger.warning(f"Profitability model not found at {self.model_path}. Profitability predictions disabled.")
            return False
        
        try:
            # Load normalization parameters
            if Path(self.norm_path).exists():
                with open(self.norm_path, 'r') as f:
                    norm_params = json.load(f)
                    self.norm_mean = np.array(norm_params['mean'], dtype=np.float32)
                    self.norm_std = np.array(norm_params['std'], dtype=np.float32)
                    # Reshape to match feature extraction output
                    if self.norm_mean.ndim == 3:
                        # Shape: (1, 60, features)
                        self.input_size = self.norm_mean.shape[2]
                    elif self.norm_mean.ndim == 2:
                        # Shape: (60, features)
                        self.input_size = self.norm_mean.shape[1]
                    else:
                        self.input_size = 20  # Default fallback
                logger.info(f"Loaded normalization parameters: input_size={self.input_size}")
            else:
                logger.warning(f"Normalization file not found at {self.norm_path}, using default normalization")
                # Use default - features will not be normalized properly
                self.input_size = 20
            
            # Initialize model
            self.model = ProfitabilityPredictor(
                input_size=self.input_size,
                hidden_size=64,
                num_layers=2,
                dropout=0.2
            ).to(self.device)
            
            # Load trained weights
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
            self.model_loaded = True
            logger.info(f"Profitability model loaded from {self.model_path} (GPU: {self.use_gpu}, input_size: {self.input_size})")
            return True
        except Exception as e:
            logger.error(f"Failed to load profitability model: {e}", exc_info=True)
            self.model_loaded = False
            return False
    
    def predict_profitability(self,
                             sol_historical: List,
                             btc_historical: Optional[List] = None) -> Optional[Dict]:
        """
        Predict if a trade would be profitable given current market conditions.
        
        Args:
            sol_historical: Recent SOL OHLCV candles (at least 60)
            btc_historical: Recent BTC OHLCV candles (optional)
            
        Returns:
            Dictionary with:
            - probability: float 0-1 (probability trade will be profitable)
            - profitable: bool (True if probability > 0.5)
            - confidence: float (normalized confidence score)
            Or None if prediction fails
        """
        if not self.model_loaded:
            if not self.load_model():
                return None
        
        if len(sol_historical) < 60:
            logger.debug(f"Insufficient historical data: {len(sol_historical)} candles (need 60)")
            return None
        
        try:
            # Extract features using the same pipeline as training
            features = extract_features(sol_historical, btc_historical)
            
            if features is None or len(features) < self.sequence_length:
                logger.debug("Feature extraction failed or insufficient features")
                return None
            
            # Use last sequence_length candles
            features_seq = features[-self.sequence_length:]  # Shape: (60, features)
            
            # Normalize if we have normalization parameters
            if self.norm_mean is not None and self.norm_std is not None:
                # Reshape to match normalization shape
                if self.norm_mean.ndim == 3:
                    # (1, 60, features) -> expand features_seq to match
                    features_seq_norm = features_seq.reshape(1, self.sequence_length, -1)
                    features_seq_norm = (features_seq_norm - self.norm_mean) / self.norm_std
                elif self.norm_mean.ndim == 2:
                    # (60, features)
                    features_seq_norm = (features_seq - self.norm_mean) / self.norm_std
                    features_seq_norm = features_seq_norm.reshape(1, self.sequence_length, -1)
                else:
                    # Fallback: just normalize
                    features_seq_norm = features_seq.reshape(1, self.sequence_length, -1)
            else:
                # No normalization available, use as-is
                features_seq_norm = features_seq.reshape(1, self.sequence_length, -1)
            
            # Ensure we have the right number of features
            if features_seq_norm.shape[2] != self.input_size:
                logger.warning(f"Feature size mismatch: got {features_seq_norm.shape[2]}, expected {self.input_size}")
                # Try to pad or truncate
                current_size = features_seq_norm.shape[2]
                if current_size < self.input_size:
                    # Pad with zeros
                    padding = np.zeros((1, self.sequence_length, self.input_size - current_size))
                    features_seq_norm = np.concatenate([features_seq_norm, padding], axis=2)
                else:
                    # Truncate
                    features_seq_norm = features_seq_norm[:, :, :self.input_size]
            
            # Convert to tensor
            features_tensor = torch.FloatTensor(features_seq_norm).to(self.device)
            
            # Make prediction
            with torch.no_grad():
                probability = self.model(features_tensor).item()
            
            # Clamp to valid range
            probability = max(0.0, min(1.0, probability))
            
            return {
                'probability': probability,
                'profitable': probability > 0.5,
                'confidence': abs(probability - 0.5) * 2  # Normalize to 0-1, with 0.5 being 0 confidence
            }
        except Exception as e:
            logger.error(f"Profitability prediction error: {e}", exc_info=True)
            return None
    
    def is_available(self) -> bool:
        """Check if profitability model is available and loaded."""
        return self.model_loaded


# Global instance (singleton pattern)
_profitability_predictor_manager = None

def get_profitability_predictor_manager(
    model_path: Optional[str] = None,
    norm_path: Optional[str] = None,
    use_gpu: bool = True
) -> ProfitabilityPredictorManager:
    """Get or create global profitability predictor manager."""
    global _profitability_predictor_manager
    if _profitability_predictor_manager is None:
        _profitability_predictor_manager = ProfitabilityPredictorManager(
            model_path, norm_path, use_gpu
        )
    return _profitability_predictor_manager

"""
Machine Learning Price Predictor using PyTorch with GPU acceleration.

This module provides LSTM and Transformer models for price prediction
that run on GPU for real-time inference.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Optional
import numpy as np

try:
    import cupy as cp
    GPU_AVAILABLE = cp.cuda.is_available()
except ImportError:
    GPU_AVAILABLE = False


class LSTMPredictor(nn.Module):
    """
    LSTM Neural Network for price prediction.
    
    Architecture:
    - Input: Historical OHLCV + technical indicators
    - LSTM layers: Capture temporal patterns
    - Attention: Focus on important time steps
    - Output: Price prediction + confidence score
    """
    
    def __init__(self, input_size=20, hidden_size=128, num_layers=2, dropout=0.2):
        super(LSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )
        
        # Output layers
        self.fc_price = nn.Linear(hidden_size, 1)  # Price prediction
        self.fc_confidence = nn.Linear(hidden_size, 1)  # Confidence score
        self.fc_direction = nn.Linear(hidden_size, 3)  # Up/Down/Hold prediction
        
    def forward(self, x):
        # x shape: (batch, sequence_length, features)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Attention mechanism
        attention_weights = self.attention(lstm_out)  # (batch, seq_len, 1)
        attention_weights = torch.softmax(attention_weights, dim=1)
        attended = torch.sum(attention_weights * lstm_out, dim=1)  # (batch, hidden_size)
        
        # Predictions
        price_pred = self.fc_price(attended)
        confidence = torch.sigmoid(self.fc_confidence(attended))
        direction = self.fc_direction(attended)
        
        return {
            'price': price_pred.squeeze(-1),
            'confidence': confidence.squeeze(-1),
            'direction': direction
        }


class TransformerPredictor(nn.Module):
    """
    Transformer model for price prediction.
    
    Better at capturing long-term dependencies than LSTM.
    """
    
    def __init__(self, input_size=20, d_model=128, nhead=8, num_layers=3, dropout=0.1):
        super(TransformerPredictor, self).__init__()
        
        self.input_projection = nn.Linear(input_size, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layers
        self.fc_price = nn.Linear(d_model, 1)
        self.fc_confidence = nn.Linear(d_model, 1)
        self.fc_direction = nn.Linear(d_model, 3)
        
    def forward(self, x):
        # Project input to model dimension
        x = self.input_projection(x)
        
        # Transformer encoding
        encoded = self.transformer(x)
        
        # Use last time step for prediction
        last_hidden = encoded[:, -1, :]
        
        # Predictions
        price_pred = self.fc_price(last_hidden)
        confidence = torch.sigmoid(self.fc_confidence(last_hidden))
        direction = self.fc_direction(last_hidden)
        
        return {
            'price': price_pred.squeeze(-1),
            'confidence': confidence.squeeze(-1),
            'direction': direction
        }


class PricePredictor:
    """
    Wrapper class for price prediction models with GPU support.
    """
    
    def __init__(self, model_type='lstm', use_gpu=True):
        self.device = torch.device('cuda' if (use_gpu and GPU_AVAILABLE) else 'cpu')
        self.model_type = model_type
        
        if model_type == 'lstm':
            self.model = LSTMPredictor().to(self.device)
        elif model_type == 'transformer':
            self.model = TransformerPredictor().to(self.device)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.model.eval()  # Set to evaluation mode
        
    def predict(self, features: np.ndarray) -> dict:
        """
        Predict price based on input features.
        
        Args:
            features: Array of shape (sequence_length, feature_count)
                     Contains OHLCV + technical indicators
            
        Returns:
            Dictionary with 'price', 'confidence', 'direction' predictions
        """
        # Convert to tensor and add batch dimension
        features_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(features_tensor)
        
        # Convert back to numpy/cpu
        result = {
            'price': predictions['price'].cpu().numpy()[0],
            'confidence': predictions['confidence'].cpu().numpy()[0],
            'direction': torch.softmax(predictions['direction'], dim=-1).cpu().numpy()[0]
        }
        
        return result
    
    def load_model(self, model_path: str):
        """Load trained model weights."""
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
    
    def save_model(self, model_path: str):
        """Save model weights."""
        torch.save(self.model.state_dict(), model_path)


# Example usage:
if __name__ == '__main__':
    # Initialize predictor
    predictor = PricePredictor(model_type='lstm', use_gpu=True)
    
    # Example features (sequence_length=60, features=20)
    example_features = np.random.randn(60, 20)
    
    # Make prediction
    prediction = predictor.predict(example_features)
    print(f"Predicted price: {prediction['price']}")
    print(f"Confidence: {prediction['confidence']:.2%}")
    print(f"Direction probabilities: {prediction['direction']}")

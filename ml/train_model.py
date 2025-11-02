"""
Train ML models for price prediction.
"""

import sys
import os
# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import asyncio
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from ml.data_collector import collect_training_data
from ml.price_predictor import LSTMPredictor, TransformerPredictor, PricePredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('train_model')


def split_data(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.8):
    """Split data into train and validation sets."""
    split_idx = int(len(X) * train_ratio)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    return X_train, X_val, y_train, y_val


def train_model(model: nn.Module, 
                X_train: np.ndarray, y_train: np.ndarray,
                X_val: np.ndarray, y_val: np.ndarray,
                epochs: int = 50,
                batch_size: int = 32,
                learning_rate: float = 0.001,
                device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
    """
    Train the model.
    
    Args:
        model: PyTorch model
        X_train: Training features (samples, sequence_length, features)
        y_train: Training targets
        X_val: Validation features
        y_val: Validation targets
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        device: 'cuda' or 'cpu'
    """
    model = model.to(device)
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train).to(device)
    y_train_t = torch.LongTensor(y_train.astype(int) + 1).to(device)  # Convert -1,0,1 to 0,1,2
    X_val_t = torch.FloatTensor(X_val).to(device)
    y_val_t = torch.LongTensor(y_val.astype(int) + 1).to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5)
    
    best_val_loss = float('inf')
    patience_counter = 0
    patience = 10
    
    logger.info(f"Training on {device} with {len(X_train)} samples...")
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        correct_train = 0
        
        # Batch training
        for i in range(0, len(X_train_t), batch_size):
            batch_X = X_train_t[i:i+batch_size]
            batch_y = y_train_t[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            
            # Extract direction logits (3 classes: down, hold, up)
            direction_logits = outputs['direction']
            loss = criterion(direction_logits, batch_y)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # Gradient clipping
            optimizer.step()
            
            train_loss += loss.item()
            pred = torch.argmax(direction_logits, dim=1)
            correct_train += (pred == batch_y).sum().item()
        
        train_acc = correct_train / len(X_train_t)
        avg_train_loss = train_loss / (len(X_train_t) // batch_size + 1)
        
        # Validation
        model.eval()
        val_loss = 0
        correct_val = 0
        
        with torch.no_grad():
            for i in range(0, len(X_val_t), batch_size):
                batch_X = X_val_t[i:i+batch_size]
                batch_y = y_val_t[i:i+batch_size]
                
                outputs = model(batch_X)
                direction_logits = outputs['direction']
                loss = criterion(direction_logits, batch_y)
                
                val_loss += loss.item()
                pred = torch.argmax(direction_logits, dim=1)
                correct_val += (pred == batch_y).sum().item()
        
        val_acc = correct_val / len(X_val_t)
        avg_val_loss = val_loss / (len(X_val_t) // batch_size + 1)
        
        scheduler.step(avg_val_loss)
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), 'models/best_model.pth')
        else:
            patience_counter += 1
        
        logger.info(f"Epoch {epoch+1}/{epochs} - "
                     f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                     f"Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}")
        
        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch+1}")
            break
    
    logger.info("Training complete!")
    logger.info(f"Best validation loss: {best_val_loss:.4f}")
    
    # Load best model
    model.load_state_dict(torch.load('models/best_model.pth'))
    return model


async def main():
    """Main training function."""
    # Create models directory
    Path('models').mkdir(exist_ok=True)
    
    # Collect data
    logger.info("Collecting training data...")
    X, y = await collect_training_data(pair='SOLUSDT', days=365, interval_minutes=60)
    
    if X is None or y is None:
        logger.error("Failed to collect data")
        return
    
    # Split data
    X_train, X_val, y_train, y_val = split_data(X, y, train_ratio=0.8)
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}")
    
    # Model parameters
    input_size = X_train.shape[2]  # Number of features
    sequence_length = X_train.shape[1]
    
    logger.info(f"Input size: {input_size}, Sequence length: {sequence_length}")
    
    # Normalize features to prevent NaN issues
    # Compute mean and std from training data only
    feature_mean = np.mean(X_train, axis=(0, 1), keepdims=True)
    feature_std = np.std(X_train, axis=(0, 1), keepdims=True) + 1e-8  # Add small epsilon
    X_train = (X_train - feature_mean) / feature_std
    X_val = (X_val - feature_mean) / feature_std
    
    # Replace any remaining NaN/Inf
    X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
    X_val = np.nan_to_num(X_val, nan=0.0, posinf=0.0, neginf=0.0)
    
    logger.info(f"Normalized features - Mean: {np.mean(feature_mean)}, Std: {np.mean(feature_std)}")
    
    # Choose model type
    model_type = 'lstm'  # or 'transformer'
    
    if model_type == 'lstm':
        model = LSTMPredictor(
            input_size=input_size,
            hidden_size=128,
            num_layers=2,
            dropout=0.2
        )
    else:
        model = TransformerPredictor(
            input_size=input_size,
            d_model=128,
            nhead=8,
            num_layers=3,
            dropout=0.1
        )
    
    # Train
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    
    trained_model = train_model(
        model, X_train, y_train, X_val, y_val,
        epochs=50,
        batch_size=32,
        learning_rate=0.0001,  # Reduced learning rate to prevent NaN
        device=device
    )
    
    # Save final model
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = f'models/price_predictor_{timestamp}.pth'
    torch.save(trained_model.state_dict(), model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Also save as default
    torch.save(trained_model.state_dict(), 'models/price_predictor.pth')
    logger.info("Model also saved as models/price_predictor.pth")


if __name__ == '__main__':
    asyncio.run(main())

#!/bin/bash
# Install GPU dependencies for SolBot

set -e

echo "SolBot GPU Setup Script"
echo "======================="
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not activated"
    echo "Please activate your venv first: source venv/bin/activate"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "Error: nvidia-smi not found. NVIDIA drivers may not be installed."
    echo "Please install NVIDIA drivers first."
    exit 1
fi

echo "Detected GPU:"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader

# Detect CUDA version
CUDA_VERSION=$(nvcc --version | grep "release" | sed 's/.*release \([0-9]\+\.[0-9]\+\).*/\1/')
echo ""
echo "Detected CUDA version: $CUDA_VERSION"

# Determine CuPy package
if [[ $(echo "$CUDA_VERSION >= 12.0" | bc -l) -eq 1 ]]; then
    CUPY_PKG="cupy-cuda12x"
elif [[ $(echo "$CUDA_VERSION >= 11.8" | bc -l) -eq 1 ]]; then
    CUPY_PKG="cupy-cuda11x"
else
    echo "Warning: CUDA version $CUDA_VERSION may not be supported"
    CUPY_PKG="cupy-cuda11x"  # Default fallback
fi

echo "Installing CuPy: $CUPY_PKG"
pip install "$CUPY_PKG"

echo ""
echo "Installing PyTorch with CUDA support..."
# Install PyTorch (adjust URL for your CUDA version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo ""
echo "Installing additional dependencies..."
pip install scikit-learn  # For data preprocessing

echo ""
echo "GPU setup complete!"
echo ""
echo "To verify installation, run:"
echo "  python -c \"import cupy as cp; print(f'CuPy: {cp.__version__}'); print(f'CUDA available: {cp.cuda.is_available()}')\""
echo "  python -c \"import torch; print(f'PyTorch CUDA: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')\""

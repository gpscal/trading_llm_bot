#!/usr/bin/env python3
"""Test CuPy import and GPU availability."""

import sys
print(f"Python: {sys.executable}")
print(f"Python version: {sys.version}")

print("\nChecking pip packages...")
import subprocess
result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
cupy_lines = [line for line in result.stdout.split('\n') if 'cupy' in line.lower()]
print("CuPy packages:", cupy_lines)

print("\nTrying to import cupy...")
try:
    import cupy as cp
    print("? CuPy imported successfully!")
    print(f"CuPy version: {cp.__version__}")
    print(f"CUDA available: {cp.cuda.is_available()}")
    if cp.cuda.is_available():
        print(f"Device count: {cp.cuda.runtime.getDeviceCount()}")
        print(f"Device name: {cp.cuda.Device(0).compute_capability}")
except ImportError as e:
    print(f"? ImportError: {e}")
    print("\nTrying alternative imports...")
    try:
        import cupy_cuda12x as cp
        print("? Imported as cupy_cuda12x")
    except Exception as e2:
        print(f"? Alternative import failed: {e2}")
except Exception as e:
    print(f"? Error: {e}")
    import traceback
    traceback.print_exc()

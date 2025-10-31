# GPU Setup Guide

Quick guide for enabling GPU acceleration with NVIDIA hardware.

## Quick Start

### Check if GPU is Available

```bash
# Check for NVIDIA GPU
nvidia-smi

# Check CUDA version
nvcc --version

# Check available ONNX Runtime providers
source venv/bin/activate
python -c "import onnxruntime; print(onnxruntime.get_available_providers())"
```

**Expected output with GPU:**
```
['CUDAExecutionProvider', 'CPUExecutionProvider']
```

## Installation

### Desktop/Server Linux with NVIDIA GPU

**1. Install CUDA (if not already installed):**

```bash
# Ubuntu/Debian
# Download from: https://developer.nvidia.com/cuda-downloads
# Or use system package manager:

# For CUDA 12.x
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-3
```

**2. Install Python dependencies:**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install GPU-enabled requirements
pip install -r requirements-gpu.txt
```

**3. Verify installation:**

```bash
python -c "import onnxruntime as ort; print('Providers:', ort.get_available_providers())"
# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider']
```

### Jetson Devices

See [JETSON_SETUP.md](JETSON_SETUP.md) for detailed Jetson-specific instructions.

**Quick install:**

```bash
# Install dependencies
pip install -r requirements.txt

# Install ONNX Runtime GPU for Jetson
pip install onnxruntime-gpu --extra-index-url https://pypi.nvidia.com
```

## Usage

### CPU Mode (Default)

```bash
python src/speak.py -f input.txt
```

Output:
```
Using CPU only
Loading Piper voice model...
   Active provider: CPUExecutionProvider
```

### GPU Mode

```bash
python src/speak.py -f input.txt --gpu
```

Output:
```
🚀 Using NVIDIA CUDA acceleration
Loading Piper voice model...
   Active provider: CUDAExecutionProvider
   ✓ CUDA acceleration enabled - expect 3-5x faster inference
```

## Performance Comparison

### Benchmark Command

```bash
# CPU benchmark
time python src/speak.py -t "$(cat examples/hello-world.txt)" -o output/cpu-bench.wav

# GPU benchmark
time python src/speak.py -t "$(cat examples/hello-world.txt)" -o output/gpu-bench.wav --gpu
```

### Expected Performance

| Hardware | Mode | Realtime Factor | Time for 10s audio |
|----------|------|----------------|-------------------|
| Modern CPU (8-core) | CPU | ~10x | ~1 second |
| RTX 3080 | GPU | ~40x | ~0.25 seconds |
| RTX 4090 | GPU | ~50x | ~0.20 seconds |
| Jetson AGX Orin | CPU | ~8x | ~1.25 seconds |
| Jetson AGX Orin | GPU | ~35x | ~0.28 seconds |
| Jetson Orin Nano | CPU | ~5x | ~2 seconds |
| Jetson Orin Nano | GPU | ~18x | ~0.55 seconds |

*Realtime factor: Higher is better (10x = generate 10 seconds of audio in 1 second)*

## Troubleshooting

### Issue: `CUDAExecutionProvider` not available

**Check CUDA installation:**
```bash
nvidia-smi
nvcc --version
echo $LD_LIBRARY_PATH | grep cuda
```

**Reinstall onnxruntime-gpu:**
```bash
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu
```

### Issue: CUDA out of memory

**Solution:** The Piper model is small, but if you have multiple processes:
```bash
# Check GPU memory
nvidia-smi

# Kill other GPU processes or reduce batch size
```

### Issue: Slower with GPU than CPU

**Possible causes:**
1. Small workload - GPU overhead > speedup (normal for very short texts)
2. PCIe bottleneck - check `nvidia-smi` for PCIe generation
3. Power limit - check `nvidia-smi` for power throttling

**Solution:**
- Use GPU for longer texts or batch processing
- For short snippets, CPU may be faster

### Issue: Falls back to CPU even with --gpu flag

**Check error messages:**
```bash
python src/speak.py -t "test" --gpu
# Look for "⚠️  Hardware acceleration initialization failed"
```

**Common fixes:**
- Install CUDA toolkit
- Check CUDA version matches onnxruntime-gpu requirements
- Verify GPU is not in use by another process

## System Requirements

### Minimum Requirements
- NVIDIA GPU with CUDA Compute Capability 3.5+
- CUDA 11.x or 12.x
- 2GB GPU memory
- Linux (Ubuntu 20.04+, Debian 11+, etc.)

### Recommended
- NVIDIA GPU with CUDA Compute Capability 7.0+ (Volta or newer)
- CUDA 12.x
- 4GB+ GPU memory
- Ubuntu 22.04 LTS

### Tested Configurations
- ✅ RTX 30xx/40xx series (Desktop)
- ✅ Jetson AGX Orin (JetPack 5.x/6.x)
- ✅ Jetson Orin Nano (JetPack 5.x/6.x)
- ✅ Tesla T4 (Server)
- ⚠️ GTX 10xx series (works, but older CUDA)
- ❌ AMD GPUs (not supported by ONNX Runtime)
- ❌ Intel GPUs (limited support)

## Advanced: Force Specific Provider

The `--gpu` flag automatically selects the best available provider. To force a specific one:

```python
# Edit src/speak.py and modify preferred_providers list
# Line ~60:
preferred_providers = ['CUDAExecutionProvider']  # Force CUDA
# or
preferred_providers = ['TensorrtExecutionProvider']  # Force TensorRT (Jetson)
```

## Further Resources

- [ONNX Runtime Execution Providers](https://onnxruntime.ai/docs/execution-providers/)
- [CUDA Installation Guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- [Jetson Setup Guide](JETSON_SETUP.md)
- [NVIDIA Developer Zone](https://developer.nvidia.com/)

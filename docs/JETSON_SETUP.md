# Jetson Setup Guide

Instructions for running Speak TTS on NVIDIA Jetson devices (AGX Orin, Orin Nano, Xavier, etc.)

## Prerequisites

### 1. JetPack Installed
Ensure you have JetPack 5.x or 6.x installed with:
- CUDA
- cuDNN
- TensorRT (optional, for maximum performance)

Check your JetPack version:
```bash
sudo apt-cache show nvidia-jetpack
```

### 2. Python 3.8+
```bash
python3 --version
```

## Installation

### Option 1: Quick Setup (Recommended for Jetson)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv portaudio19-dev

# Clone/navigate to the speak directory
cd /path/to/speak

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (CPU version first)
pip install -r requirements.txt

# Install ONNX Runtime GPU for Jetson
# Use the JetPack-compatible wheel from NVIDIA
pip install onnxruntime-gpu --extra-index-url https://pypi.nvidia.com
```

### Option 2: Using Pre-built ONNX Runtime (JetPack 5.x/6.x)

For Jetson devices, NVIDIA provides optimized ONNX Runtime builds:

```bash
# Check your JetPack version and architecture
# For JetPack 5.1.x / 6.x on ARM64:

# Install from NVIDIA's repository
pip install onnxruntime-gpu==1.17.1 --extra-index-url https://pypi.nvidia.com

# Or download specific wheel for your platform
# Visit: https://elinux.org/Jetson_Zoo#ONNX_Runtime
```

### Option 3: Build from Source (Advanced)

If pre-built wheels don't work:

```bash
# This takes ~1-2 hours on Jetson
git clone --recursive https://github.com/Microsoft/onnxruntime
cd onnxruntime
./build.sh --config Release --update --build --parallel \
  --use_cuda --cuda_home /usr/local/cuda \
  --cudnn_home /usr/lib/aarch64-linux-gnu \
  --build_wheel

pip install build/Linux/Release/dist/*.whl
```

## Download Voice Model

```bash
# Create models directory
mkdir -p models
cd models

# Download default model
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

cd ..
```

## Verify GPU Support

```bash
# Check if CUDA is detected
python3 -c "import onnxruntime as ort; print('Available providers:', ort.get_available_providers())"

# You should see: ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
# Or at minimum: ['CUDAExecutionProvider', 'CPUExecutionProvider']
```

## Usage

### Test CPU Mode (Default)
```bash
source venv/bin/activate
python src/speak.py -f examples/hello-world.txt
```

### Enable GPU Acceleration
```bash
# Use --gpu flag for CUDA acceleration
python src/speak.py -f examples/hello-world.txt --gpu

# You should see: "🚀 Using NVIDIA CUDA acceleration"
```

### Benchmark Performance
```bash
# CPU mode
time python src/speak.py -t "Testing CPU performance with a longer sentence to measure inference time."

# GPU mode
time python src/speak.py -t "Testing GPU performance with a longer sentence to measure inference time." --gpu

# Expect 3-5x speedup with GPU on Jetson devices
```

## Performance Tips

### 1. Enable Maximum Performance Mode
```bash
# Set Jetson to maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 2. Monitor GPU Usage
```bash
# In another terminal
sudo tegrastats

# Watch GPU utilization during TTS generation
```

### 3. Increase Swap (if needed)
For Orin Nano with limited RAM:
```bash
# Create 8GB swap file
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 4. Batch Processing
Process multiple files to amortize model loading:
```bash
# Create a batch script
for file in input_texts/*.txt; do
    python src/speak.py -f "$file" -o "output/$(basename "$file" .txt).wav" --gpu
done
```

## Troubleshooting

### Issue: `CUDAExecutionProvider` not available

**Solution:**
```bash
# Verify CUDA installation
nvcc --version
ls /usr/local/cuda/lib64/libcudart.so*

# Reinstall onnxruntime-gpu
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu --extra-index-url https://pypi.nvidia.com
```

### Issue: Out of memory errors

**Solution:**
```bash
# Use smaller batch sizes or close other applications
# Monitor memory:
free -h

# Kill memory-intensive processes
sudo systemctl stop desktop-manager  # If running headless
```

### Issue: Slow inference even with GPU

**Possible causes:**
1. Model not actually running on GPU - check logs for "Active provider: CUDAExecutionProvider"
2. Power mode not set to maximum - run `sudo nvpmodel -m 0`
3. CPU governor throttling - run `sudo jetson_clocks`
4. Thermal throttling - check temperature with `tegrastats`

### Issue: Audio playback not working

**Solution:**
```bash
# Install audio libraries
sudo apt install -y portaudio19-dev python3-pyaudio alsa-utils

# Test audio output
speaker-test -t wav -c 2

# If no audio device, just generate files without -p flag
python src/speak.py -f input.txt  # No playback, just save to file
```

## Expected Performance

| Device | Mode | Speed (realtime factor) |
|--------|------|------------------------|
| Jetson AGX Orin | CPU | ~8-10x realtime |
| Jetson AGX Orin | GPU | ~30-40x realtime |
| Jetson Orin Nano | CPU | ~4-6x realtime |
| Jetson Orin Nano | GPU | ~15-20x realtime |

*Realtime factor: Higher is better (10x means 10 seconds of audio generated per 1 second of time)*

## Resources

- [NVIDIA Jetson Zoo](https://elinux.org/Jetson_Zoo)
- [JetPack Documentation](https://docs.nvidia.com/jetson/)
- [ONNX Runtime for Jetson](https://github.com/microsoft/onnxruntime/blob/main/BUILD.md#jetson)
- [Piper Voice Models](https://github.com/rhasspy/piper-voices)

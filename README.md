# Speak - Text-to-Speech CLI

Convert text to natural-sounding speech using Piper TTS. Fast, offline, and privacy-friendly.

**Features:**
- 🎤 High-quality neural TTS using Piper
- 🚀 GPU acceleration support (NVIDIA CUDA)
- 🔒 Privacy-friendly (runs completely offline)
- ⚡ Fast inference (real-time on CPU, 3-5x faster with GPU)
- 🎮 Perfect for Jetson devices (AGX Orin, Orin Nano)

## Quick Start

### 1. Install Dependencies

**CPU-only (Default):**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**With GPU support (NVIDIA/Jetson):**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install GPU-enabled packages
pip install -r requirements-gpu.txt

# For Jetson devices, see docs/JETSON_SETUP.md
```

### 2. Run Your First Conversion

```bash
# Convert the example file
python src/speak.py -f examples/hello-world.txt

# Output will be saved to: output/speech.wav
```

### 3. Try More Examples

```bash
# Convert custom text
python src/speak.py -t "Hello, this is Piper speaking!"

# Convert and play immediately
python src/speak.py -f examples/hello-world.txt -p

# Custom output location
python src/speak.py -t "Test" -o my-speech.wav
```

## Usage

```bash
python src/speak.py [OPTIONS]

Options:
  -f, --file PATH        Input text file to convert
  -t, --text TEXT        Text string to convert (alternative to --file)
  -o, --output PATH      Output WAV file path (default: output/speech.wav)
  -m, --model PATH       Path to custom Piper model (optional)
  -p, --play             Play audio after generation
  --gpu                  Enable GPU acceleration (NVIDIA CUDA/TensorRT)
  --help                 Show help message
```

## GPU Acceleration

Enable GPU acceleration for 3-5x faster inference on NVIDIA GPUs:

```bash
# CPU mode (default, works everywhere)
python src/speak.py -f input.txt

# GPU mode (NVIDIA GPUs, Jetson devices)
python src/speak.py -f input.txt --gpu
```

**Expected output with GPU:**
```
🚀 Using NVIDIA CUDA acceleration
Loading Piper voice model from models/en_US-lessac-medium.onnx...
   Active provider: CUDAExecutionProvider
   ✓ CUDA acceleration enabled - expect 3-5x faster inference
```

**Supported platforms:**
- ✅ NVIDIA Desktop/Server GPUs (RTX, GTX, Tesla, etc.)
- ✅ NVIDIA Jetson (AGX Orin, Orin Nano, Xavier, TX2)
- ❌ AMD GPUs (not supported by ONNX Runtime)
- ❌ Apple Silicon (CoreML incompatible with Piper models)

**Setup GPU support:**
- See [Jetson Setup Guide](docs/JETSON_SETUP.md) for Jetson devices
- For desktop Linux: Install CUDA 11.x/12.x, then use `requirements-gpu.txt`

## Features

- **High-quality neural TTS** using Piper
- **Works offline** - no API keys or internet required after initial setup
- **Fast generation** - real-time on CPU, 3-5x faster with GPU
- **Privacy-friendly** - all processing happens locally
- **Multiple voices** - support for custom Piper models
- **Simple CLI** - easy to use and script
- **GPU acceleration** - NVIDIA CUDA/TensorRT support

## Requirements

- Python 3.8+
- ~100MB disk space for default voice model (auto-downloaded on first use)

## Project Structure

```
speak/
├── src/
│   └── speak.py          # Main CLI application
├── examples/
│   └── hello-world.txt   # Example input file
├── output/               # Generated audio files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Advanced Usage

### Using Different Voice Models

Download additional models from [Piper Voices](https://github.com/rhasspy/piper-voices):

```bash
# Download a model
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json

# Use it
python src/speak.py -f text.txt -m en_US-amy-medium.onnx
```

### Batch Processing

```bash
# Process multiple files
for file in texts/*.txt; do
    python src/speak.py -f "$file" -o "output/$(basename "$file" .txt).wav"
done
```

## Troubleshooting

**Import errors after installation:**
- Make sure your virtual environment is activated
- Try: `pip install --upgrade -r requirements.txt`

**Audio playback not working:**
- macOS: Should work out of the box
- Linux: `sudo apt-get install portaudio19-dev`
- Or skip playback and just generate files (don't use `-p`)

**First run is slow:**
- The voice model is being downloaded (happens once)
- Subsequent runs will be much faster

## Documentation

See [CLAUDE.md](claude.md) for detailed documentation including:
- Development workflow
- Code style conventions
- Testing guidelines
- Architecture details
- Contributing guidelines

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Links

- [Piper TTS](https://github.com/rhasspy/piper)
- [Piper Voice Models](https://github.com/rhasspy/piper-voices)

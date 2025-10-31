# Speak - Text-to-Speech CLI

## Overview
A simple, high-quality text-to-speech (TTS) CLI tool powered by Piper TTS. Convert text files or strings to natural-sounding speech using local neural TTS models. Works offline, fast, and privacy-friendly.

## Project Structure
```
/
├── src/           # Source code
│   ├── speak.py   # Main CLI application
│   └── __init__.py
├── tests/         # Test files
├── examples/      # Example text files
│   └── hello-world.txt
├── output/        # Generated audio files (gitignored)
├── config/        # Configuration files
└── requirements.txt
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- ffmpeg (optional, for audio format conversion)

### Installation
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally
```bash
# Convert text file to speech
python src/speak.py -f examples/hello-world.txt

# Convert text string to speech
python src/speak.py -t "Hello, this is a test" -o output/test.wav

# Convert and play immediately
python src/speak.py -f examples/hello-world.txt -p
```

## Development Workflow

### Branch Strategy
- `main` - production-ready code
- `develop` - integration branch
- `feature/*` - new features
- `bugfix/*` - bug fixes

### Commit Convention
Follow conventional commits:
- `feat:` - new feature
- `fix:` - bug fix
- `refactor:` - code refactoring
- `docs:` - documentation changes
- `test:` - test additions/changes
- `chore:` - maintenance tasks

## Code Style & Conventions

### Language-Specific Guidelines
- Follow PEP 8 Python style guide
- Use type hints for function signatures
- Docstrings for all functions and classes
- Max line length: 100 characters
- Use f-strings for string formatting

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Code Organization
- Keep functions small and focused
- Single responsibility principle
- DRY (Don't Repeat Yourself)
- Write self-documenting code

## Testing

### Running Tests
```bash
pytest                    # Run all tests
pytest -v                 # Verbose mode
pytest --cov=src          # Coverage report
pytest -k test_name       # Run specific test
```

### Testing Guidelines
- Write tests for all new features
- Use pytest for testing framework
- Test edge cases and error handling
- Mock external dependencies (Piper models)
- Use meaningful test descriptions

## Architecture

### Design Patterns
- CLI-based application using Click framework
- Functional programming approach
- Separation of concerns (CLI, TTS engine, audio handling)

### Key Components
- **speak.py**: Main CLI application and entry point (src/speak.py)
- **load_piper_voice()**: Voice model loader with caching
- **text_to_speech()**: Core TTS conversion function
- **CLI handler**: Click-based command-line interface

### Data Flow
1. User provides text (file or string via CLI)
2. Text is read and validated
3. Piper voice model is loaded (cached after first load)
4. Text is synthesized to audio waveform
5. Audio is saved as WAV file
6. Optionally played through system audio

## CLI Usage

### Commands
```bash
# Basic usage
speak -f <file>                    # Convert text file
speak -t "text"                    # Convert text string
speak -o <output.wav>              # Specify output file
speak -m <model.onnx>              # Use custom voice model
speak -p                           # Play audio after generation
speak --gpu                        # Enable GPU acceleration (NVIDIA)

# Combined options
speak -f input.txt -o speech.wav -p
speak -t "Hello world" --play
speak -f input.txt --gpu           # Use NVIDIA CUDA acceleration
```

### Examples
```bash
# Convert hello-world.txt to speech
python src/speak.py -f examples/hello-world.txt

# Custom output location
python src/speak.py -f story.txt -o audiobooks/story.wav

# Quick test with playback
python src/speak.py -t "Testing Piper TTS" -p

# GPU-accelerated conversion (NVIDIA/Jetson)
python src/speak.py -f examples/hello-world.txt --gpu
```

## Configuration

### Piper Models
Models are automatically downloaded on first use. Default: `en_US-lessac-medium`

Available models:
- `en_US-lessac-medium` - Default, good quality, medium speed
- `en_US-lessac-high` - High quality, slower
- `en_US-amy-medium` - Alternative voice
- Many more at: https://github.com/rhasspy/piper

### Custom Models
```bash
# Download a model manually
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

# Use custom model
python src/speak.py -f text.txt -m path/to/model.onnx
```

## Deployment

### Build
```bash
npm run build
```

### Production
```bash
npm start
```

### Environments
- **Development**: https://dev.example.com
- **Staging**: https://staging.example.com
- **Production**: https://example.com

## Common Commands

```bash
# Development
python src/speak.py --help              # Show help
python src/speak.py -f examples/hello-world.txt  # Test basic functionality

# Code quality
black src/                              # Format code
flake8 src/                             # Lint code
mypy src/                               # Type checking
pytest                                  # Run tests

# Virtual environment
python3 -m venv venv                    # Create venv
source venv/bin/activate                # Activate (Unix)
deactivate                              # Deactivate
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'piper'`
**Solution**: Ensure virtual environment is activated and run `pip install -r requirements.txt`

**Issue**: Audio playback not working
**Solution**: Install system audio libraries:
- macOS: Should work out of the box
- Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`
- Windows: Install PyAudio wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/

**Issue**: Model download fails
**Solution**: Check internet connection or download model manually from Piper voices repository

**Issue**: Poor audio quality
**Solution**: Try a higher quality model using `-m` flag with a `-high` variant model

## Performance Considerations
- Use lazy loading for routes
- Implement caching where appropriate
- Optimize database queries
- Monitor bundle size

## Security Best Practices
- Never commit secrets or API keys
- Validate all user input
- Use parameterized queries
- Keep dependencies updated
- Implement rate limiting

## Contributing

### Pull Request Process
1. Create feature branch from `develop`
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description
6. Request review from team members

### Code Review Guidelines
- Check for code quality and style
- Verify test coverage
- Ensure documentation is updated
- Validate security implications

## Dependencies

### Key Libraries
- **piper-tts**: Neural text-to-speech engine (>=1.2.0)
- **click**: CLI framework for command-line interface (>=8.1.0)
- **sounddevice**: Audio playback library (>=0.4.6)
- **soundfile**: Audio file I/O (>=0.12.1)
- **numpy**: Audio data processing (>=1.24.0)
- **onnxruntime**: CPU inference engine (included with piper-tts)
- **onnxruntime-gpu**: GPU inference engine (optional, for NVIDIA GPUs)

### Installation Options

**CPU-only (default):**
```bash
pip install -r requirements.txt
```

**GPU support (NVIDIA/Jetson):**
```bash
# Desktop Linux with NVIDIA GPU
pip install -r requirements-gpu.txt

# Jetson devices (see docs/JETSON_SETUP.md)
pip install onnxruntime-gpu --extra-index-url https://pypi.nvidia.com
```

### Updating Dependencies
```bash
pip list --outdated              # Check for updates
pip install --upgrade piper-tts  # Update specific package
pip install -r requirements.txt --upgrade  # Update all
```

## Performance Considerations
- First run may be slower due to model download
- Models are cached after first load for faster subsequent runs
- WAV files can be large - consider compressing to MP3 for storage
- Batch processing: Process multiple files in a loop for efficiency

### GPU Acceleration
- **CPU mode**: ~8-10x realtime on modern CPUs
- **GPU mode (NVIDIA)**: ~30-40x realtime (3-5x speedup over CPU)
- **Jetson AGX Orin**: ~30-40x realtime with --gpu flag
- **Jetson Orin Nano**: ~15-20x realtime with --gpu flag
- GPU acceleration requires CUDA 11.x or 12.x installed
- See `docs/JETSON_SETUP.md` for Jetson-specific optimizations

## Resources
- [Piper TTS GitHub](https://github.com/rhasspy/piper)
- [Piper Voice Models](https://github.com/rhasspy/piper-voices)
- [Click Documentation](https://click.palletsprojects.com/)

## Future Enhancements
- [ ] Support for additional audio formats (MP3, OGG)
- [ ] Batch processing of multiple files
- [ ] Voice selection menu
- [ ] SSML support for prosody control
- [ ] REST API wrapper
- [ ] GUI interface

## License
MIT License - see [LICENSE.md](LICENSE.md) for full text

## Contributing
Contributions welcome! Please follow the development workflow and code style conventions outlined above.

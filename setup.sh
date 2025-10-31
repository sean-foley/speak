#!/bin/bash

# Speak TTS - Quick Setup Script

set -e

echo "🎤 Setting up Speak TTS..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create output directory
mkdir -p output
echo "✓ Output directory created"

# Run test
echo ""
echo "Running test conversion..."
python src/speak.py -f examples/hello-world.txt -o output/hello-world.wav
echo ""
echo "✓ Test successful!"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run: python src/speak.py -f examples/hello-world.txt -p"
echo ""
echo "For more options: python src/speak.py --help"

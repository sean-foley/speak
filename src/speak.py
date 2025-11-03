#!/usr/bin/env python3
"""
Speak - A simple text-to-speech CLI using Piper TTS

Copyright (c) 2025 Sean Foley
Licensed under the MIT License - see LICENSE.md for details
"""

import os
import sys
import time
from pathlib import Path
import fcntl  # Unix file locking
import click
import sounddevice as sd
import soundfile as sf
import numpy as np


class SpeakLock:
    """
    File-based lock to prevent concurrent speak instances.
    Uses fcntl (Unix/Linux) for advisory file locking.
    """
    def __init__(self, lockfile_path: str = "/tmp/speak.lock", timeout: float = None, fail_if_locked: bool = False):
        self.lockfile_path = lockfile_path
        self.timeout = timeout
        self.fail_if_locked = fail_if_locked
        self.lockfile = None

    def __enter__(self):
        self.lockfile = open(self.lockfile_path, 'w')

        if self.fail_if_locked:
            # Non-blocking - fail immediately if locked
            try:
                fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                self.lockfile.close()
                raise RuntimeError("Another speak instance is already running. Skipping.")
        elif self.timeout:
            # Try to acquire lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError:
                    if time.time() - start_time > self.timeout:
                        self.lockfile.close()
                        raise TimeoutError(f"Could not acquire lock after {self.timeout}s. Another instance is running.")
                    time.sleep(0.1)
        else:
            # Blocking - wait indefinitely
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX)

        # Write PID to lockfile for debugging
        self.lockfile.write(f"{os.getpid()}\n")
        self.lockfile.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lockfile:
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)
            self.lockfile.close()
            # Optionally remove lockfile
            try:
                os.unlink(self.lockfile_path)
            except:
                pass


def load_piper_voice(model_path: str = None, use_gpu: bool = False):
    """
    Load Piper TTS voice model

    Args:
        model_path: Path to .onnx model file. If None, uses default.
        use_gpu: Whether to use GPU/NPU acceleration if available.

    Returns:
        PiperVoice instance
    """
    try:
        from piper import PiperVoice
        import onnxruntime as ort
    except ImportError:
        click.echo("Error: piper-tts not installed. Run: pip install piper-tts", err=True)
        sys.exit(1)

    if model_path and os.path.exists(model_path):
        click.echo(f"Loading custom voice model: {model_path}")
        voice_path = model_path
    else:
        # Use default model from models directory
        default_model = "models/en_US-lessac-medium.onnx"
        script_dir = Path(__file__).parent.parent
        full_model_path = script_dir / default_model

        if not full_model_path.exists():
            click.echo(f"Error: Default model not found at {full_model_path}", err=True)
            click.echo("\nTo download the model, run:", err=True)
            click.echo("  mkdir -p models", err=True)
            click.echo("  cd models", err=True)
            click.echo('  curl -L -O "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"', err=True)
            click.echo('  curl -L -O "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"', err=True)
            sys.exit(1)

        voice_path = str(full_model_path)

    # Determine execution providers for hardware acceleration
    if use_gpu:
        available_providers = ort.get_available_providers()

        # Priority order: CUDA (NVIDIA) > TensorRT (Jetson optimized) > CPU
        preferred_providers = []

        if 'CUDAExecutionProvider' in available_providers:
            preferred_providers.append('CUDAExecutionProvider')
            click.echo("🚀 Using NVIDIA CUDA acceleration")
        elif 'TensorrtExecutionProvider' in available_providers:
            preferred_providers.append('TensorrtExecutionProvider')
            click.echo("🚀 Using NVIDIA TensorRT acceleration (optimized for Jetson)")
        elif 'CoreMLExecutionProvider' in available_providers:
            # CoreML available but not recommended for Piper
            click.echo("⚠️  CoreML detected but not compatible with Piper models")
            click.echo("   Falling back to CPU (use --gpu at your own risk)")
            preferred_providers = ['CPUExecutionProvider']
        else:
            click.echo("⚠️  No GPU acceleration available, falling back to CPU")
            preferred_providers = ['CPUExecutionProvider']

        # Always add CPU as fallback
        if 'CPUExecutionProvider' not in preferred_providers:
            preferred_providers.append('CPUExecutionProvider')
    else:
        preferred_providers = ['CPUExecutionProvider']
        click.echo("Using CPU only")

    click.echo(f"Loading Piper voice model from {voice_path}...")

    # Load voice with specified providers
    # Note: PiperVoice.load() doesn't expose providers, so we load and patch
    voice = PiperVoice.load(voice_path)

    # Attempt to reload the ONNX session with hardware acceleration
    try:
        import onnxruntime as ort
        sess_options = ort.SessionOptions()
        # Suppress verbose logging
        sess_options.log_severity_level = 3

        voice.session = ort.InferenceSession(
            voice_path,
            sess_options=sess_options,
            providers=preferred_providers
        )
        actual_providers = voice.session.get_providers()
        click.echo(f"   Active provider: {actual_providers[0]}")

        # Show performance tip for CUDA users
        if 'CUDAExecutionProvider' in actual_providers:
            click.echo("   ✓ CUDA acceleration enabled - expect 3-5x faster inference")

    except Exception as e:
        click.echo(f"   ⚠️  Hardware acceleration initialization failed: {str(e)[:100]}")
        click.echo("   Falling back to CPU...")
        # Fallback to CPU-only
        try:
            voice.session = ort.InferenceSession(
                voice_path,
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            click.echo("   ✓ CPU fallback successful")
        except Exception as cpu_err:
            click.echo(f"   ❌ CPU fallback failed: {cpu_err}", err=True)
            raise

    return voice


def text_to_speech(text: str, output_file: str, model_path: str = None, play_audio: bool = False, use_gpu: bool = False):
    """
    Convert text to speech and save as WAV file

    Args:
        text: Text to convert to speech
        output_file: Output WAV file path
        model_path: Optional path to Piper model
        play_audio: Whether to play the audio after generation
    """
    click.echo(f"Converting text to speech...")

    # Load voice model
    voice = load_piper_voice(model_path, use_gpu=use_gpu)

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate speech - collect all audio chunks
    audio_arrays = []
    sample_rate = None

    for audio_chunk in voice.synthesize(text):
        audio_arrays.append(audio_chunk.audio_int16_array)
        if sample_rate is None:
            sample_rate = audio_chunk.sample_rate

    # Concatenate all audio chunks
    if audio_arrays:
        audio_data = np.concatenate(audio_arrays)
    else:
        click.echo("Error: No audio generated", err=True)
        sys.exit(1)

    # Write to WAV file
    sf.write(str(output_path), audio_data, sample_rate)
    click.echo(f"✓ Audio saved to: {output_path}")

    # Play audio if requested
    if play_audio:
        click.echo("Playing audio...")
        sd.play(audio_data, sample_rate)
        sd.wait()
        click.echo("✓ Playback complete")

    return str(output_path)


@click.command()
@click.option('-f', '--file', 'input_file', type=click.Path(exists=True),
              help='Input text file to convert to speech')
@click.option('-t', '--text', help='Text to convert to speech (alternative to --file)')
@click.option('-o', '--output', default='output/speech.wav',
              help='Output WAV file path (default: output/speech.wav)')
@click.option('-m', '--model', 'model_path', type=click.Path(exists=True),
              help='Path to Piper .onnx model file (optional)')
@click.option('--no-play', is_flag=True, help='Save to file only (skip audio playback)')
@click.option('--gpu', is_flag=True, help='Enable GPU acceleration (CUDA/TensorRT for NVIDIA)')
@click.option('--no-lock', is_flag=True, help='Disable process locking (allow concurrent instances)')
@click.option('--lock-timeout', type=float, default=None,
              help='Lock timeout in seconds (default: wait indefinitely)')
@click.option('--skip-if-locked', is_flag=True,
              help='Skip if another instance is running (for MQTT/queue scenarios)')
def main(input_file, text, output, model_path, no_play, gpu, no_lock, lock_timeout, skip_if_locked):
    """
    Speak - Convert text to speech using Piper TTS

    Examples:
        speak -f examples/hello-world.txt
        speak -t "Hello, world!" -o output/hello.wav
        speak -f input.txt --no-play  # Save only, don't play
    """
    # Validate input
    if not input_file and not text:
        click.echo("Error: Must provide either --file or --text", err=True)
        click.echo("Run 'speak --help' for usage information")
        sys.exit(1)

    # Get text content
    if input_file:
        click.echo(f"Reading from: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read().strip()
    else:
        text_content = text

    if not text_content:
        click.echo("Error: No text to convert", err=True)
        sys.exit(1)

    click.echo(f"Text: {text_content[:100]}..." if len(text_content) > 100 else f"Text: {text_content}")

    # Convert to speech with optional locking
    try:
        if no_lock:
            # No locking - allow concurrent instances
            text_to_speech(text_content, output, model_path, not no_play, use_gpu=gpu)
        else:
            # Use file lock to prevent concurrent instances
            lock = SpeakLock(
                timeout=lock_timeout,
                fail_if_locked=skip_if_locked
            )
            try:
                with lock:
                    text_to_speech(text_content, output, model_path, not no_play, use_gpu=gpu)
            except RuntimeError as e:
                # Another instance is running and --skip-if-locked was used
                click.echo(f"⏭️  {e}", err=True)
                sys.exit(2)  # Exit code 2 = skipped
            except TimeoutError as e:
                # Lock timeout exceeded
                click.echo(f"⏱️  {e}", err=True)
                sys.exit(3)  # Exit code 3 = timeout
    except Exception as e:
        click.echo(f"Error during conversion: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

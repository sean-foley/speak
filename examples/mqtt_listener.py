#!/usr/bin/env python3
"""
MQTT to TTS Bridge

Listens to MQTT topics and converts messages to speech using Speak CLI.
Handles concurrent messages gracefully with built-in locking.

Copyright (c) 2025 Sean Foley
Licensed under the MIT License
"""

import paho.mqtt.client as mqtt
import subprocess
import logging
import argparse
from pathlib import Path

# Default configuration
DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "tts/speak"
DEFAULT_STRATEGY = "skip"  # "skip", "timeout", or "queue"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSBridge:
    """MQTT to TTS bridge with concurrent request handling"""

    def __init__(self, speak_path: str, use_gpu: bool = False, strategy: str = "skip"):
        self.speak_path = Path(speak_path)
        self.use_gpu = use_gpu
        self.strategy = strategy
        self.message_count = 0
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0

    def speak(self, text: str) -> bool:
        """
        Convert text to speech with configured strategy

        Args:
            text: Text to convert to speech

        Returns:
            True if spoken successfully, False otherwise
        """
        cmd = ['python3', str(self.speak_path), '-t', text]

        if self.use_gpu:
            cmd.append('--gpu')

        if self.strategy == "skip":
            cmd.append('--skip-if-locked')
        elif self.strategy == "timeout":
            cmd.extend(['--lock-timeout', '30'])
        # "queue" strategy uses default blocking behavior

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute max
            )

            if result.returncode == 0:
                logger.info(f"✓ Spoke: '{text[:60]}{'...' if len(text) > 60 else ''}'")
                self.success_count += 1
                return True
            elif result.returncode == 2:
                logger.warning(f"⏭️  Skipped (busy): '{text[:40]}'")
                self.skip_count += 1
                return False
            elif result.returncode == 3:
                logger.warning(f"⏱️  Timeout: '{text[:40]}'")
                self.skip_count += 1
                return False
            else:
                logger.error(f"❌ TTS error: {result.stderr.strip()}")
                self.error_count += 1
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"⏱️  Process timeout: '{text[:40]}'")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            self.error_count += 1
            return False

    def print_stats(self):
        """Print statistics"""
        logger.info(f"📊 Stats: {self.message_count} received, "
                   f"{self.success_count} spoken, "
                   f"{self.skip_count} skipped, "
                   f"{self.error_count} errors")


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    bridge = userdata['bridge']
    topic = userdata['topic']

    if rc == 0:
        logger.info(f"✓ Connected to MQTT broker")
        client.subscribe(topic)
        logger.info(f"📡 Subscribed to: {topic}")
        logger.info(f"🔧 Strategy: {bridge.strategy}, GPU: {bridge.use_gpu}")
    else:
        logger.error(f"❌ Connection failed with code {rc}")


def on_disconnect(client, userdata, rc):
    """MQTT disconnect callback"""
    if rc != 0:
        logger.warning(f"⚠️  Unexpected disconnect (code {rc})")


def on_message(client, userdata, msg):
    """MQTT message callback"""
    bridge = userdata['bridge']

    try:
        text = msg.payload.decode('utf-8').strip()
        if text:
            bridge.message_count += 1
            logger.info(f"📥 [{bridge.message_count}] Received from {msg.topic}")
            bridge.speak(text)

            # Print stats every 10 messages
            if bridge.message_count % 10 == 0:
                bridge.print_stats()
    except Exception as e:
        logger.error(f"❌ Message handling error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='MQTT to TTS Bridge - Convert MQTT messages to speech'
    )
    parser.add_argument('-b', '--broker', default=DEFAULT_BROKER,
                       help=f'MQTT broker address (default: {DEFAULT_BROKER})')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_PORT,
                       help=f'MQTT broker port (default: {DEFAULT_PORT})')
    parser.add_argument('-t', '--topic', default=DEFAULT_TOPIC,
                       help=f'MQTT topic to subscribe (default: {DEFAULT_TOPIC})')
    parser.add_argument('-s', '--speak-path', default='src/speak.py',
                       help='Path to speak.py (default: src/speak.py)')
    parser.add_argument('--gpu', action='store_true',
                       help='Enable GPU acceleration for TTS')
    parser.add_argument('--strategy', choices=['skip', 'timeout', 'queue'],
                       default=DEFAULT_STRATEGY,
                       help='Concurrent message strategy (default: skip)')
    parser.add_argument('-u', '--username', help='MQTT username (optional)')
    parser.add_argument('--password', help='MQTT password (optional)')

    args = parser.parse_args()

    # Verify speak.py exists
    speak_path = Path(args.speak_path)
    if not speak_path.exists():
        logger.error(f"❌ speak.py not found at: {speak_path}")
        logger.error(f"   Current directory: {Path.cwd()}")
        return 1

    # Create TTS bridge
    bridge = TTSBridge(
        speak_path=args.speak_path,
        use_gpu=args.gpu,
        strategy=args.strategy
    )

    # Setup MQTT client
    client = mqtt.Client(userdata={'bridge': bridge, 'topic': args.topic})
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    if args.username:
        client.username_pw_set(args.username, args.password)

    try:
        logger.info(f"🔌 Connecting to {args.broker}:{args.port}")
        client.connect(args.broker, args.port, keepalive=60)

        logger.info("🎤 MQTT to TTS Bridge running... (Ctrl+C to stop)")
        client.loop_forever()

    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")
        bridge.print_stats()
        client.disconnect()
        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())

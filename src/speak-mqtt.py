#!/usr/bin/env python3
"""
MQTT to TTS Bridge - Listen to MQTT topics and convert messages to speech

Copyright (c) 2025 Sean Foley
Licensed under the MIT License - see LICENSE.md for details
"""

import sys
import signal
import subprocess
from pathlib import Path
import click
import paho.mqtt.client as mqtt


class MQTTTTSBridge:
    """Simple MQTT to TTS bridge"""

    def __init__(self, broker, port, topic, username=None, password=None, speak_args=None):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.username = username
        self.password = password
        self.speak_args = speak_args or []
        self.client = None
        self.running = True

        # Get path to speak.py (same directory as this script)
        self.speak_path = Path(__file__).parent / "speak.py"

    def on_connect(self, client, _userdata, _flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            click.echo(f"✓ Connected to {self.broker}:{self.port}")
            client.subscribe(self.topic)
            click.echo(f"✓ Subscribed to topic: {self.topic}")
        else:
            click.echo(f"✗ Connection failed with code {rc}", err=True)
            sys.exit(1)

    def on_message(self, _client, _userdata, msg):
        """Callback when message received"""
        try:
            text = msg.payload.decode('utf-8').strip()
            if not text:
                return

            click.echo(f"📥 Received: {text[:80]}{'...' if len(text) > 80 else ''}")

            # Build command to call speak.py
            cmd = ['python3', str(self.speak_path), '-t', text] + self.speak_args

            # Execute speak.py
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                click.echo(f"✓ Spoken")
            elif result.returncode == 2:
                click.echo(f"⏭️  Skipped (busy)")
            else:
                click.echo(f"✗ Error: {result.stderr.strip()}", err=True)

        except Exception as e:
            click.echo(f"✗ Error processing message: {e}", err=True)

    def on_disconnect(self, _client, _userdata, rc):
        """Callback when disconnected"""
        if rc != 0 and self.running:
            click.echo(f"⚠️  Disconnected unexpectedly (code {rc})", err=True)

    def signal_handler(self, _signum, _frame):
        """Handle Ctrl+C and SIGTERM"""
        click.echo("\n👋 Shutting down...")
        self.running = False
        if self.client:
            self.client.disconnect()
        sys.exit(0)

    def run(self):
        """Start the MQTT listener loop"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Verify speak.py exists
        if not self.speak_path.exists():
            click.echo(f"✗ Error: speak.py not found at {self.speak_path}", err=True)
            return 1

        # Setup MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Set credentials if provided
        if self.username:
            self.client.username_pw_set(self.username, self.password)

        try:
            click.echo(f"🔌 Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)

            click.echo("🎤 MQTT to TTS Bridge running... (Ctrl+C to stop)")

            # Run forever (until Ctrl+C or SIGTERM)
            self.client.loop_forever()

        except Exception as e:
            click.echo(f"✗ Fatal error: {e}", err=True)
            return 1

        return 0


@click.command()
@click.option('-s', '--server', required=True,
              help='MQTT broker address (required)')
@click.option('-t', '--topic', required=True,
              help='MQTT topic to subscribe (required)')
@click.option('-p', '--port', type=int, default=1883,
              help='MQTT broker port (default: 1883)')
@click.option('-u', '--username',
              help='MQTT username (optional)')
@click.option('-P', '--password',
              help='MQTT password (optional)')
@click.option('--gpu', is_flag=True,
              help='Enable GPU acceleration for speak.py')
@click.option('--skip-if-locked', is_flag=True,
              help='Skip TTS if another instance is running')
@click.option('--lock-timeout', type=float,
              help='Lock timeout in seconds')
@click.option('--no-lock', is_flag=True,
              help='Disable locking (allow concurrent instances)')
@click.option('-o', '--output',
              help='Output file path for speak.py')
def main(server, topic, port, username, password, gpu, skip_if_locked, lock_timeout, no_lock, output):
    """
    MQTT to TTS Bridge - Convert MQTT messages to speech

    Listens to an MQTT topic and converts incoming messages to speech using speak.py.
    Runs continuously until Ctrl+C or SIGTERM.

    Examples:

        speak-mqtt -s mqtt.example.com -t tts/speak

        speak-mqtt -s localhost -p 1883 -t home/tts -u user -P pass

        speak-mqtt -s mqtt.local -t alerts --gpu --skip-if-locked
    """
    # Build arguments to pass to speak.py
    speak_args = []
    if gpu:
        speak_args.append('--gpu')
    if skip_if_locked:
        speak_args.append('--skip-if-locked')
    if lock_timeout:
        speak_args.extend(['--lock-timeout', str(lock_timeout)])
    if no_lock:
        speak_args.append('--no-lock')
    if output:
        speak_args.extend(['-o', output])

    # Create and run bridge
    bridge = MQTTTTSBridge(
        broker=server,
        port=port,
        topic=topic,
        username=username,
        password=password,
        speak_args=speak_args
    )

    sys.exit(bridge.run())


if __name__ == '__main__':
    sys.exit(main())

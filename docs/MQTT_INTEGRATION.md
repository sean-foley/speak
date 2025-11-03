# MQTT Integration Guide

How to use Speak TTS with MQTT message queues for concurrent-safe text-to-speech.

## Problem: Concurrent TTS Requests

When multiple MQTT messages arrive quickly, naive shell execution would create:
- ❌ Multiple TTS instances fighting for GPU/CPU
- ❌ Overlapping audio playback
- ❌ Wasted resources loading model multiple times
- ❌ Potential system overload

## Solution: Built-in Locking

Speak includes three mutual exclusion strategies:

### Strategy 1: Skip if Busy (Recommended for MQTT) ⭐

**Best for:** High-frequency messages where dropping some is acceptable

```bash
# Skip if another instance is already running
python src/speak.py -t "Alert: Temperature high" --skip-if-locked

# Exit codes:
# 0 = Success
# 2 = Skipped (another instance running)
# 1 = Error
```

**MQTT Python Example:**
```python
import paho.mqtt.client as mqtt
import subprocess

def on_message(client, userdata, msg):
    text = msg.payload.decode('utf-8')

    # Non-blocking: Skip if busy
    result = subprocess.run(
        ['python', 'src/speak.py', '-t', text, '--skip-if-locked', '--gpu'],
        capture_output=True
    )

    if result.returncode == 0:
        print(f"✓ Spoke: {text}")
    elif result.returncode == 2:
        print(f"⏭️  Skipped (busy): {text}")
    else:
        print(f"❌ Error: {result.stderr.decode()}")

client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt.example.com", 1883)
client.subscribe("tts/speak")
client.loop_forever()
```

---

### Strategy 2: Wait with Timeout

**Best for:** Important messages that should be queued but not forever

```bash
# Wait up to 30 seconds for lock
python src/speak.py -t "Important alert" --lock-timeout 30

# Exit codes:
# 0 = Success
# 3 = Timeout (waited too long)
# 1 = Error
```

**MQTT Example:**
```python
def on_message(client, userdata, msg):
    text = msg.payload.decode('utf-8')

    # Wait up to 10 seconds
    result = subprocess.run(
        ['python', 'src/speak.py', '-t', text, '--lock-timeout', '10', '--gpu'],
        capture_output=True,
        timeout=15  # Kill if hung
    )

    if result.returncode == 0:
        print(f"✓ Spoke: {text}")
    elif result.returncode == 3:
        print(f"⏱️  Timeout: {text}")
```

---

### Strategy 3: Wait Indefinitely (Queue)

**Best for:** All messages must be spoken, order matters

```bash
# Wait as long as needed (creates queue)
python src/speak.py -t "Message 1"  # Default behavior
python src/speak.py -t "Message 2"  # Waits for Message 1
python src/speak.py -t "Message 3"  # Waits for Message 2
```

**MQTT Example (with thread pool):**
```python
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt
import subprocess

# Single-threaded executor = queue
executor = ThreadPoolExecutor(max_workers=1)

def speak_text(text):
    """Blocking TTS call"""
    result = subprocess.run(
        ['python', 'src/speak.py', '-t', text, '--gpu'],
        capture_output=True
    )
    return result.returncode == 0

def on_message(client, userdata, msg):
    text = msg.payload.decode('utf-8')
    # Submit to queue (non-blocking for MQTT)
    executor.submit(speak_text, text)
    print(f"📥 Queued: {text}")

client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt.example.com", 1883)
client.subscribe("tts/speak")
client.loop_forever()
```

---

## Complete MQTT Listener Example

Full production-ready example with error handling:

```python
#!/usr/bin/env python3
"""
MQTT to TTS Bridge
Subscribes to MQTT topics and converts messages to speech
"""

import paho.mqtt.client as mqtt
import subprocess
import logging
from pathlib import Path

# Configuration
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 1883
MQTT_TOPIC = "tts/speak"
SPEAK_CMD = ["python3", "/path/to/speak/src/speak.py"]
USE_GPU = True
STRATEGY = "skip"  # "skip", "timeout", or "queue"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def speak(text: str, strategy: str = "skip") -> bool:
    """
    Convert text to speech with specified locking strategy

    Returns:
        True if spoken, False if skipped/error
    """
    cmd = SPEAK_CMD + ['-t', text]

    if USE_GPU:
        cmd.append('--gpu')

    if strategy == "skip":
        cmd.append('--skip-if-locked')
    elif strategy == "timeout":
        cmd.extend(['--lock-timeout', '30'])
    # "queue" strategy uses default (wait indefinitely)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Kill if hung
        )

        if result.returncode == 0:
            logger.info(f"✓ Spoke: {text[:50]}")
            return True
        elif result.returncode == 2:
            logger.warning(f"⏭️  Skipped (busy): {text[:50]}")
            return False
        elif result.returncode == 3:
            logger.warning(f"⏱️  Timeout: {text[:50]}")
            return False
        else:
            logger.error(f"❌ Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Process timeout: {text[:50]}")
        return False
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        return False


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        logger.info(f"Connected to MQTT broker: {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    """MQTT message callback"""
    try:
        text = msg.payload.decode('utf-8').strip()
        if text:
            logger.info(f"📥 Received: {text[:50]}")
            speak(text, strategy=STRATEGY)
    except Exception as e:
        logger.error(f"Message handling error: {e}")


def main():
    """Main MQTT listener loop"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        logger.info("Starting MQTT loop...")
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
```

---

## Testing Lock Behavior

### Test concurrent instances:

**Terminal 1:**
```bash
python src/speak.py -t "This is a long message that will take several seconds to convert to speech" --gpu
```

**Terminal 2 (while Terminal 1 is running):**
```bash
# This will skip
python src/speak.py -t "Quick message" --skip-if-locked

# This will wait
python src/speak.py -t "Quick message" --lock-timeout 10

# This will queue
python src/speak.py -t "Quick message"
```

### Simulate MQTT load:

```bash
# Send 10 messages rapidly
for i in {1..10}; do
    python src/speak.py -t "Message $i" --skip-if-locked &
done
wait

# Only the first should succeed, others skip
```

---

## Lock File Location

Default: `/tmp/speak.lock`

To customize:
```python
# Modify SpeakLock() call in speak.py
lock = SpeakLock(
    lockfile_path="/var/run/speak.lock",  # Custom location
    timeout=lock_timeout,
    fail_if_locked=skip_if_locked
)
```

---

## Exit Codes Reference

| Code | Meaning | When |
|------|---------|------|
| 0 | Success | TTS completed successfully |
| 1 | Error | Conversion failed, invalid input, etc. |
| 2 | Skipped | Another instance running (--skip-if-locked) |
| 3 | Timeout | Lock timeout exceeded (--lock-timeout) |

Use in shell scripts:
```bash
python src/speak.py -t "test" --skip-if-locked
case $? in
    0) echo "Success" ;;
    2) echo "Skipped" ;;
    3) echo "Timeout" ;;
    *) echo "Error" ;;
esac
```

---

## Performance Notes

- **Lock overhead**: < 1ms (negligible)
- **Skip check**: Non-blocking (instant)
- **Timeout mode**: Polls every 100ms
- **Queue mode**: Efficient (no polling)

## Troubleshooting

**Issue**: Lock not working (concurrent instances run anyway)

**Solution**: Check lock file permissions
```bash
ls -la /tmp/speak.lock
# Should be writable by your user
```

**Issue**: Lock file not cleaned up

**Solution**: Safe to delete manually
```bash
rm /tmp/speak.lock
# Lock is advisory, will be recreated
```

**Issue**: "Another instance running" but no process found

**Solution**: Stale lock file
```bash
# Check PID in lock file
cat /tmp/speak.lock
# If process doesn't exist, remove lock
rm /tmp/speak.lock
```

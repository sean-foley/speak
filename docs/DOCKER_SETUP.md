# Docker Setup Guide

Run Speak TTS MQTT Bridge in Docker containers across multiple platforms.

## Supported Platforms

✅ **Mac** (Intel and Apple Silicon)
✅ **Linux** (x86_64, ARM64)
✅ **NVIDIA Jetson AGX Orin** (ARM64 + GPU)
✅ **NVIDIA Jetson Orin Nano** (ARM64 + GPU)

## Quick Start

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Example `.env`:**
```bash
MQTT_SERVER=mqtt.example.com
MQTT_PORT=1883
MQTT_TOPIC=tts/speak
MQTT_USERNAME=myuser
MQTT_PASSWORD=mypassword
USE_GPU=false
SKIP_IF_LOCKED=true
```

### 2. Build and Run

**CPU version (Mac, Linux):**
```bash
docker-compose up -d speak-mqtt-cpu
```

**GPU version (Jetson devices):**
```bash
docker-compose up -d speak-mqtt-gpu
```

### 3. View Logs

```bash
# CPU version
docker-compose logs -f speak-mqtt-cpu

# GPU version
docker-compose logs -f speak-mqtt-gpu
```

### 4. Stop

```bash
docker-compose down
```

---

## Platform-Specific Instructions

### Mac (Intel or Apple Silicon)

**Prerequisites:**
- Docker Desktop for Mac
- Audio output device

**Build:**
```bash
# Build CPU image
docker-compose build speak-mqtt-cpu

# Run
docker-compose up -d speak-mqtt-cpu
```

**Note:** GPU support not available on Mac.

---

### Linux (x86_64 or ARM64)

**Prerequisites:**
- Docker Engine
- ALSA audio libraries
- For GPU: NVIDIA drivers and nvidia-docker2

**CPU version:**
```bash
docker-compose up -d speak-mqtt-cpu
```

**GPU version (NVIDIA GPU):**
```bash
# Install nvidia-docker2 first
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Build and run
docker-compose up -d speak-mqtt-gpu
```

---

### NVIDIA Jetson AGX Orin / Orin Nano

**Prerequisites:**
- JetPack 5.x or 6.x
- Docker installed
- NVIDIA Container Runtime

**Setup Docker (if not already installed):**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Runtime
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**Configure for GPU:**
```bash
# Edit .env file
cat > .env <<EOF
MQTT_SERVER=mqtt.example.com
MQTT_PORT=1883
MQTT_TOPIC=tts/speak
USE_GPU=true
SKIP_IF_LOCKED=true
EOF
```

**Build and Run:**
```bash
# Build GPU image (uses Jetson-optimized base)
docker-compose build speak-mqtt-gpu

# Run
docker-compose up -d speak-mqtt-gpu

# View logs
docker-compose logs -f speak-mqtt-gpu
```

**Expected output:**
```
🔌 Connecting to mqtt.example.com:1883...
✓ Connected to mqtt.example.com:1883
✓ Subscribed to topic: tts/speak
🎤 MQTT to TTS Bridge running... (Ctrl+C to stop)
```

---

## Manual Docker Commands

### Build Images

**CPU image:**
```bash
docker build --build-arg PLATFORM=cpu -t speak-mqtt:cpu .
```

**GPU image:**
```bash
docker build --build-arg PLATFORM=gpu -t speak-mqtt:gpu .
```

### Run Containers

**CPU version:**
```bash
docker run -d \
  --name speak-mqtt-cpu \
  --restart unless-stopped \
  --device /dev/snd \
  -e MQTT_SERVER=mqtt.example.com \
  -e MQTT_PORT=1883 \
  -e MQTT_TOPIC=tts/speak \
  -e USE_GPU=false \
  -e SKIP_IF_LOCKED=true \
  -v $(pwd)/output:/app/output \
  speak-mqtt:cpu
```

**GPU version (Jetson):**
```bash
docker run -d \
  --name speak-mqtt-gpu \
  --runtime nvidia \
  --restart unless-stopped \
  --device /dev/snd \
  -e MQTT_SERVER=mqtt.example.com \
  -e MQTT_PORT=1883 \
  -e MQTT_TOPIC=tts/speak \
  -e USE_GPU=true \
  -e SKIP_IF_LOCKED=true \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -v $(pwd)/output:/app/output \
  speak-mqtt:gpu
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MQTT_SERVER` | ✅ Yes | localhost | MQTT broker address |
| `MQTT_PORT` | No | 1883 | MQTT broker port |
| `MQTT_TOPIC` | ✅ Yes | tts/speak | MQTT topic to subscribe |
| `MQTT_USERNAME` | No | - | MQTT username (optional) |
| `MQTT_PASSWORD` | No | - | MQTT password (optional) |
| `USE_GPU` | No | false | Enable GPU acceleration |
| `SKIP_IF_LOCKED` | No | false | Skip if instance running |

---

## Audio Device Access

### Linux/Jetson

The container needs access to `/dev/snd` for audio playback:

```yaml
devices:
  - /dev/snd:/dev/snd
```

**Verify audio devices:**
```bash
# On host
aplay -l

# In container
docker exec speak-mqtt-cpu aplay -l
```

### Mac

Docker Desktop for Mac automatically handles audio device passthrough.

---

## Testing

### Test MQTT Messages

**Using mosquitto_pub:**
```bash
# Send test message
mosquitto_pub -h mqtt.example.com -t tts/speak -m "Hello from MQTT"

# Container should log:
# 📥 Received: Hello from MQTT
# ✓ Spoken
```

**Using Python:**
```python
import paho.mqtt.publish as publish

publish.single(
    "tts/speak",
    payload="Testing Docker TTS",
    hostname="mqtt.example.com",
    port=1883
)
```

---

## Troubleshooting

### Issue: No audio output

**Check audio devices:**
```bash
# Host
ls -la /dev/snd

# Container
docker exec speak-mqtt-cpu ls -la /dev/snd
```

**Solution:**
```bash
# Ensure user has audio group permissions
sudo usermod -aG audio $USER
newgrp audio

# Rebuild and restart
docker-compose down
docker-compose up -d
```

---

### Issue: GPU not detected (Jetson)

**Check NVIDIA runtime:**
```bash
docker info | grep -i nvidia
# Should show: Runtimes: nvidia
```

**Solution:**
```bash
# Install/reinstall nvidia-docker2
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Set default runtime to nvidia
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

```bash
sudo systemctl restart docker
```

---

### Issue: Container exits immediately

**Check logs:**
```bash
docker-compose logs speak-mqtt-cpu
```

**Common causes:**
- MQTT server unreachable
- Invalid credentials
- speak.py not found

---

### Issue: High CPU usage

**Check if GPU is actually being used:**
```bash
# On Jetson
sudo tegrastats

# In container
docker exec speak-mqtt-gpu python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should include: CUDAExecutionProvider
```

---

## Performance Optimization

### Jetson Devices

**Enable maximum performance mode:**
```bash
# Before starting container
sudo nvpmodel -m 0
sudo jetson_clocks

# Then start container
docker-compose up -d speak-mqtt-gpu
```

### CPU Limits

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for faster processing
      memory: 4G
```

---

## Building for Multiple Platforms

### Using Docker Buildx

```bash
# Create builder
docker buildx create --name multiplatform --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg PLATFORM=cpu \
  -t yourusername/speak-mqtt:cpu \
  --push \
  .
```

---

## Production Deployment

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml speak-tts
```

### Kubernetes

See `docs/KUBERNETES.md` (if needed).

---

## Health Monitoring

**Check container health:**
```bash
docker inspect speak-mqtt-cpu --format='{{.State.Health.Status}}'
```

**Health check endpoint** (built-in):
- Checks if `speak-mqtt.py` process is running
- Interval: 30 seconds
- Timeout: 10 seconds

---

## Logging

**View real-time logs:**
```bash
docker-compose logs -f speak-mqtt-cpu
```

**Export logs:**
```bash
docker-compose logs speak-mqtt-cpu > speak-mqtt.log
```

**Rotate logs** (docker-compose.yml):
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Updates

**Pull latest changes:**
```bash
git pull

# Rebuild images
docker-compose build

# Restart containers
docker-compose down
docker-compose up -d
```

---

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi speak-mqtt:cpu speak-mqtt:gpu

# Remove volumes (caution: deletes output files)
docker-compose down -v
```

# Multi-platform Dockerfile for Speak TTS MQTT Bridge
# Supports: amd64 (Mac/Linux), arm64 (Mac M1/M2, Jetson)
# GPU support: NVIDIA CUDA (Jetson AGX Orin, Jetson Orin Nano)

ARG PLATFORM=cpu
ARG PYTHON_VERSION=3.10

# ============================================================================
# Stage 1: Base image (CPU-only)
# ============================================================================
FROM python:${PYTHON_VERSION}-slim AS base-cpu

LABEL maintainer="Sean Foley"
LABEL description="Speak TTS MQTT Bridge - CPU version"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libsndfile1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-mqtt.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-mqtt.txt

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/

# Create output directory
RUN mkdir -p output models

# Download default Piper model
RUN mkdir -p models && \
    cd models && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# ============================================================================
# Stage 2: NVIDIA GPU image (for Jetson devices)
# ============================================================================
FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3 AS base-gpu

LABEL maintainer="Sean Foley"
LABEL description="Speak TTS MQTT Bridge - GPU version for Jetson"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    alsa-utils \
    libsndfile1 \
    wget \
    curl \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-mqtt.txt ./

# Install Python dependencies (without onnxruntime, will use Jetson's)
RUN pip3 install --no-cache-dir click numpy sounddevice soundfile paho-mqtt

# Install ONNX Runtime GPU for Jetson
RUN pip3 install --no-cache-dir onnxruntime-gpu --extra-index-url https://pypi.nvidia.com || \
    echo "Warning: Could not install onnxruntime-gpu, using CPU version"

# Install piper-tts
RUN pip3 install --no-cache-dir piper-tts

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/

# Create output directory
RUN mkdir -p output models

# Download default Piper model
RUN mkdir -p models && \
    cd models && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# ============================================================================
# Final stage selection
# ============================================================================
FROM base-${PLATFORM} AS final

WORKDIR /app

# Environment variables (can be overridden)
ENV MQTT_SERVER=localhost
ENV MQTT_PORT=1883
ENV MQTT_TOPIC=tts/speak
ENV MQTT_USERNAME=""
ENV MQTT_PASSWORD=""
ENV USE_GPU=false
ENV SKIP_IF_LOCKED=false

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Build command with environment variables\n\
CMD="python3 src/speak-mqtt.py -s ${MQTT_SERVER} -p ${MQTT_PORT} -t ${MQTT_TOPIC}"\n\
\n\
# Add optional parameters\n\
if [ -n "${MQTT_USERNAME}" ]; then\n\
    CMD="${CMD} -u ${MQTT_USERNAME}"\n\
fi\n\
\n\
if [ -n "${MQTT_PASSWORD}" ]; then\n\
    CMD="${CMD} -P ${MQTT_PASSWORD}"\n\
fi\n\
\n\
if [ "${USE_GPU}" = "true" ]; then\n\
    CMD="${CMD} --gpu"\n\
fi\n\
\n\
if [ "${SKIP_IF_LOCKED}" = "true" ]; then\n\
    CMD="${CMD} --skip-if-locked"\n\
fi\n\
\n\
# Add any additional arguments passed to container\n\
CMD="${CMD} $@"\n\
\n\
echo "Starting MQTT TTS Bridge..."\n\
echo "Command: ${CMD}"\n\
exec ${CMD}\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose no ports (MQTT client only)
EXPOSE 0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f speak-mqtt.py || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []

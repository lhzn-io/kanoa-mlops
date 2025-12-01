#!/bin/bash
# -----------------------------------------------------------------------------
# kanoa-mlops vLLM Startup Script
# Runs on GCE instance boot to configure and start vLLM server
# -----------------------------------------------------------------------------

set -euo pipefail

# Logging setup
exec > >(tee -a /var/log/kanoa-startup.log) 2>&1
echo "=========================================="
echo "kanoa-mlops startup script"
echo "Started at: $(date)"
echo "=========================================="

# -----------------------------------------------------------------------------
# Read configuration from instance metadata
# -----------------------------------------------------------------------------
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
METADATA_HEADER="Metadata-Flavor: Google"

get_metadata() {
    curl -sf -H "$METADATA_HEADER" "$METADATA_URL/$1" || echo "$2"
}

MODEL_NAME=$(get_metadata "model-name" "allenai/Molmo-7B-D-0924")
VLLM_IMAGE=$(get_metadata "vllm-image" "vllm/vllm-openai:v0.6.3.post1")
MAX_MODEL_LEN=$(get_metadata "max-model-len" "4096")
GPU_MEMORY_UTIL=$(get_metadata "gpu-memory-utilization" "0.9")
IDLE_TIMEOUT=$(get_metadata "idle-timeout-minutes" "30")
HF_TOKEN=$(get_metadata "hf-token" "")

echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  vLLM Image: $VLLM_IMAGE"
echo "  Max Model Len: $MAX_MODEL_LEN"
echo "  GPU Memory Util: $GPU_MEMORY_UTIL"
echo "  Idle Timeout: $IDLE_TIMEOUT minutes"

# -----------------------------------------------------------------------------
# Install Docker (if not present)
# -----------------------------------------------------------------------------
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# -----------------------------------------------------------------------------
# Install NVIDIA Container Toolkit (if not present)
# -----------------------------------------------------------------------------
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    echo "Installing NVIDIA Container Toolkit..."
    distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
        gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L "https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list" | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# Verify GPU access
echo "Verifying GPU access..."
nvidia-smi || { echo "ERROR: GPU not accessible"; exit 1; }

# -----------------------------------------------------------------------------
# Pull vLLM image
# -----------------------------------------------------------------------------
echo "Pulling vLLM image: $VLLM_IMAGE"
docker pull "$VLLM_IMAGE"

# -----------------------------------------------------------------------------
# Stop existing container (if any)
# -----------------------------------------------------------------------------
docker rm -f kanoa-vllm 2>/dev/null || true

# -----------------------------------------------------------------------------
# Start vLLM container
# -----------------------------------------------------------------------------
echo "Starting vLLM server..."

DOCKER_ARGS=(
    -d
    --name kanoa-vllm
    --gpus all
    --restart unless-stopped
    -p 8000:8000
    -v /root/.cache/huggingface:/root/.cache/huggingface:rw
)

# Add HF token if provided
if [ -n "$HF_TOKEN" ]; then
    DOCKER_ARGS+=(-e "HF_TOKEN=$HF_TOKEN")
fi

VLLM_ARGS=(
    --model "$MODEL_NAME"
    --host 0.0.0.0
    --port 8000
    --served-model-name "$MODEL_NAME"
    --trust-remote-code
    --max-model-len "$MAX_MODEL_LEN"
    --gpu-memory-utilization "$GPU_MEMORY_UTIL"
)

docker run "${DOCKER_ARGS[@]}" "$VLLM_IMAGE" "${VLLM_ARGS[@]}"

echo "vLLM container started"

# -----------------------------------------------------------------------------
# Setup Idle Shutdown Daemon
# -----------------------------------------------------------------------------
if [ "$IDLE_TIMEOUT" -gt 0 ]; then
    echo "Setting up idle shutdown daemon (timeout: $IDLE_TIMEOUT minutes)..."

    cat > /opt/kanoa-idle-shutdown.sh << 'IDLE_SCRIPT'
#!/bin/bash
# Idle shutdown daemon for kanoa-mlops
# Monitors vLLM API activity and shuts down VM after inactivity

IDLE_TIMEOUT_MINUTES=${1:-30}
IDLE_TIMEOUT_SECONDS=$((IDLE_TIMEOUT_MINUTES * 60))
CHECK_INTERVAL=60
LAST_ACTIVITY_FILE="/tmp/kanoa-last-activity"
HEALTH_ENDPOINT="http://localhost:8000/health"
LOG_FILE="/var/log/kanoa-idle-shutdown.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Initialize last activity time
date +%s > "$LAST_ACTIVITY_FILE"
log "Idle shutdown daemon started (timeout: $IDLE_TIMEOUT_MINUTES minutes)"

while true; do
    sleep $CHECK_INTERVAL

    # Check if vLLM is healthy
    if ! curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        log "vLLM health check failed, skipping activity check"
        continue
    fi

    # Check for recent requests in Docker logs
    # Look for HTTP request patterns in the last minute
    RECENT_REQUESTS=$(docker logs --since=1m kanoa-vllm 2>&1 | \
        grep -cE '"(POST|GET) /v1/(chat/completions|completions|models)"' || echo 0)

    if [ "$RECENT_REQUESTS" -gt 0 ]; then
        date +%s > "$LAST_ACTIVITY_FILE"
        log "Activity detected: $RECENT_REQUESTS requests"
    fi

    # Calculate idle time
    LAST_ACTIVITY=$(cat "$LAST_ACTIVITY_FILE" 2>/dev/null || date +%s)
    NOW=$(date +%s)
    IDLE_SECONDS=$((NOW - LAST_ACTIVITY))
    IDLE_MINUTES=$((IDLE_SECONDS / 60))

    if [ "$IDLE_SECONDS" -ge "$IDLE_TIMEOUT_SECONDS" ]; then
        log "Idle for $IDLE_MINUTES minutes (threshold: $IDLE_TIMEOUT_MINUTES), initiating shutdown"
        
        # Stop vLLM container gracefully
        docker stop kanoa-vllm || true
        
        # Shutdown the VM
        shutdown -h now "Idle shutdown after $IDLE_MINUTES minutes of inactivity"
        exit 0
    fi
done
IDLE_SCRIPT

    chmod +x /opt/kanoa-idle-shutdown.sh

    # Create systemd service for idle shutdown
    cat > /etc/systemd/system/kanoa-idle-shutdown.service << EOF
[Unit]
Description=kanoa-mlops Idle Shutdown Daemon
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/opt/kanoa-idle-shutdown.sh $IDLE_TIMEOUT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable kanoa-idle-shutdown
    systemctl start kanoa-idle-shutdown

    echo "Idle shutdown daemon started"
fi

# -----------------------------------------------------------------------------
# Wait for vLLM to be ready
# -----------------------------------------------------------------------------
echo "Waiting for vLLM server to be ready..."
MAX_WAIT=600  # 10 minutes (model loading can take a while)
WAIT_INTERVAL=10
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "vLLM server is ready!"
        echo "API endpoint: http://$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip):8000"
        exit 0
    fi
    echo "  Waiting for vLLM... ($ELAPSED/$MAX_WAIT seconds)"
    sleep $WAIT_INTERVAL
    ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

echo "WARNING: vLLM server did not become ready within $MAX_WAIT seconds"
echo "Check logs with: docker logs kanoa-vllm"
exit 1

#!/bin/bash
set -e

echo "🚀 Setting up LabDabbler Codespace Environment..."

# Function to log with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if this is an update run
UPDATE_MODE=false
if [[ "$1" == "--update" ]]; then
    UPDATE_MODE=true
    log "Running in update mode..."
fi

# Wait for Docker daemon to be ready
log "Waiting for Docker daemon to start..."
until docker info >/dev/null 2>&1; do
    log "Docker daemon not ready yet, waiting..."
    sleep 2
done
log "✅ Docker daemon is ready"

# Update package lists
log "Updating package lists..."
sudo apt-get update -qq

# Install essential packages
log "Installing essential packages..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    jq \
    unzip \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    apt-transport-https \
    build-essential \
    python3-dev \
    python3-pip \
    golang-go \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    bridge-utils \
    iptables \
    dnsutils \
    telnet \
    ssh \
    openssh-client \
    vim \
    nano \
    htop \
    tree \
    make

# Install Go (required for containerlab)
log "Installing Go..."
GO_VERSION="1.21.6"
if ! command -v go &> /dev/null || [[ "$UPDATE_MODE" == "true" ]]; then
    wget -q "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
    rm "go${GO_VERSION}.linux-amd64.tar.gz"
    
    # Add Go to PATH for current session and future sessions
    export PATH=$PATH:/usr/local/go/bin
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
fi
log "✅ Go installed: $(go version)"

# Install containerlab
log "Installing containerlab..."
CONTAINERLAB_VERSION="${CONTAINERLAB_VERSION:-0.56.0}"
if ! command -v containerlab &> /dev/null || [[ "$UPDATE_MODE" == "true" ]]; then
    # Download and install containerlab
    wget -q "https://github.com/srl-labs/containerlab/releases/download/v${CONTAINERLAB_VERSION}/containerlab_${CONTAINERLAB_VERSION}_linux_amd64.tar.gz"
    tar -zxf "containerlab_${CONTAINERLAB_VERSION}_linux_amd64.tar.gz"
    sudo mv containerlab /usr/local/bin/
    rm "containerlab_${CONTAINERLAB_VERSION}_linux_amd64.tar.gz"
    sudo chmod +x /usr/local/bin/containerlab
fi
log "✅ Containerlab installed: $(containerlab version --detail)"

# Install yq (YAML processor)
log "Installing yq..."
if ! command -v yq &> /dev/null || [[ "$UPDATE_MODE" == "true" ]]; then
    sudo wget -qO /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64"
    sudo chmod +x /usr/local/bin/yq
fi
log "✅ yq installed: $(yq --version)"

# Setup Python environment
log "Setting up Python environment..."
cd /workspaces/labdabbler

# Install uv (fast Python package manager)
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
fi

# Install Python dependencies using uv
log "Installing Python dependencies..."
if [[ -f "pyproject.toml" ]]; then
    ~/.cargo/bin/uv sync
    log "✅ Python dependencies installed via uv"
else
    # Fallback to pip if no pyproject.toml
    pip3 install --user fastapi uvicorn aiohttp aiofiles docker pyyaml requests jinja2 python-multipart httpx
    log "✅ Python dependencies installed via pip"
fi

# Setup Node.js environment
log "Setting up Node.js environment..."
cd /workspaces/labdabbler/web/frontend

# Install frontend dependencies
if [[ -f "package.json" ]]; then
    npm install
    log "✅ Frontend dependencies installed"
fi

# Create necessary directories
log "Creating necessary directories..."
cd /workspaces/labdabbler
mkdir -p data/{vm_images,vrnetlab_builds,container_registry,lab_configs}
mkdir -p logs
mkdir -p configs/{devices,services,startup-configs}

# Set proper permissions
sudo chown -R vscode:vscode /workspaces/labdabbler
sudo chown -R vscode:docker /var/run/docker.sock 2>/dev/null || true

# Add vscode user to docker group
sudo usermod -aG docker vscode

# Pre-pull common container images for faster lab startup
log "Pre-pulling common container images..."
COMMON_IMAGES=(
    "ghcr.io/nokia/srlinux:latest"
    "frrouting/frr:latest"
    "alpine:latest"
    "ubuntu:22.04"
    "nginx:latest"
    "busybox:latest"
)

for image in "${COMMON_IMAGES[@]}"; do
    log "Pulling $image..."
    docker pull "$image" &
done

# Wait for all background pulls to complete
wait

# Setup git configuration if not already set
if [[ -z "$(git config --global user.name)" ]]; then
    git config --global user.name "Codespace User"
    git config --global user.email "user@codespace.local"
    log "✅ Git configured with default user"
fi

# Create example lab if it doesn't exist
EXAMPLE_LAB="labs/examples/basic-srlinux-lab.clab.yml"
if [[ ! -f "$EXAMPLE_LAB" ]]; then
    log "Creating example lab configuration..."
    mkdir -p labs/examples
    cat > "$EXAMPLE_LAB" << 'EOF'
name: basic-srlinux-lab

topology:
  nodes:
    srl1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd2
      startup-config: |
        set / interface ethernet-1/1 admin-state enable
        set / interface ethernet-1/1 subinterface 0 admin-state enable
        set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
        set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.1/24
    
    srl2:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd2
      startup-config: |
        set / interface ethernet-1/1 admin-state enable
        set / interface ethernet-1/1 subinterface 0 admin-state enable
        set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
        set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.0.2/24

  links:
    - endpoints: ["srl1:e1-1", "srl2:e1-1"]
EOF
    log "✅ Example lab created at $EXAMPLE_LAB"
fi

# Create helpful aliases
log "Setting up helpful aliases..."
cat >> ~/.bashrc << 'EOF'

# LabDabbler aliases
alias ll='ls -la'
alias lab='containerlab'
alias labdeploy='containerlab deploy'
alias labdestroy='containerlab destroy'
alias lablist='containerlab inspect --all'
alias labstatus='docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"'
alias backend='cd /workspaces/labdabbler/web/backend && python app.py'
alias frontend='cd /workspaces/labdabbler/web/frontend && npm run dev'
alias logs='cd /workspaces/labdabbler && find logs -name "*.log" -exec tail -f {} +'

# Docker helpers
alias dps='docker ps'
alias dimg='docker images'
alias dnet='docker network ls'
alias dvol='docker volume ls'

# Quick navigation
alias cdlab='cd /workspaces/labdabbler'
alias cdlabs='cd /workspaces/labdabbler/labs'
alias cdback='cd /workspaces/labdabbler/web/backend'
alias cdfront='cd /workspaces/labdabbler/web/frontend'
EOF

# Create a startup script for the entire application
log "Creating startup script..."
cat > /workspaces/labdabbler/start-labdabbler.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting LabDabbler application..."

# Ensure Docker is running
sudo service docker start

# Start backend in background
echo "Starting FastAPI backend..."
cd /workspaces/labdabbler/web/backend
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start frontend in background
echo "Starting React frontend..."
cd /workspaces/labdabbler/web/frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ LabDabbler started!"
echo "🌐 Frontend: http://localhost:5000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop LabDabbler: pkill -f 'python app.py' && pkill -f 'npm run dev'"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Keep script running
wait
EOF

chmod +x /workspaces/labdabbler/start-labdabbler.sh

# Create containerlab completion
log "Setting up containerlab auto-completion..."
containerlab completion bash | sudo tee /etc/bash_completion.d/containerlab > /dev/null

# Enable IP forwarding for containerlab networking
log "Enabling IP forwarding..."
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Configure bridge networking
log "Configuring bridge networking..."
sudo modprobe bridge
sudo modprobe br_netfilter

# Create helpful scripts
log "Creating helper scripts..."
mkdir -p /workspaces/labdabbler/.devcontainer/scripts

# Lab management script
cat > /workspaces/labdabbler/.devcontainer/scripts/lab-helper.sh << 'EOF'
#!/bin/bash
# LabDabbler Lab Helper Script

case "$1" in
    "start")
        echo "🚀 Starting LabDabbler services..."
        /workspaces/labdabbler/start-labdabbler.sh
        ;;
    "stop")
        echo "🛑 Stopping LabDabbler services..."
        pkill -f 'python app.py' 2>/dev/null || true
        pkill -f 'npm run dev' 2>/dev/null || true
        echo "✅ Services stopped"
        ;;
    "status")
        echo "📊 LabDabbler Status:"
        echo "Backend: $(pgrep -f 'python app.py' >/dev/null && echo '✅ Running' || echo '❌ Stopped')"
        echo "Frontend: $(pgrep -f 'npm run dev' >/dev/null && echo '✅ Running' || echo '❌ Stopped')"
        echo ""
        echo "Active Labs:"
        containerlab inspect --all 2>/dev/null || echo "No active labs"
        ;;
    "labs")
        echo "📋 Available Labs:"
        find /workspaces/labdabbler/labs -name "*.clab.yml" -exec basename {} \; | sort
        ;;
    "deploy")
        if [[ -z "$2" ]]; then
            echo "Usage: lab-helper deploy <lab-file>"
            exit 1
        fi
        echo "🚀 Deploying lab: $2"
        containerlab deploy -t "$2"
        ;;
    "destroy")
        if [[ -z "$2" ]]; then
            echo "Usage: lab-helper destroy <lab-file>"
            exit 1
        fi
        echo "🗑️ Destroying lab: $2"
        containerlab destroy -t "$2"
        ;;
    *)
        echo "LabDabbler Lab Helper"
        echo "Usage: lab-helper {start|stop|status|labs|deploy <file>|destroy <file>}"
        echo ""
        echo "Commands:"
        echo "  start     - Start LabDabbler backend and frontend"
        echo "  stop      - Stop LabDabbler services"
        echo "  status    - Show service and lab status"
        echo "  labs      - List available lab files"
        echo "  deploy    - Deploy a specific lab"
        echo "  destroy   - Destroy a specific lab"
        ;;
esac
EOF

chmod +x /workspaces/labdabbler/.devcontainer/scripts/lab-helper.sh

# Add lab-helper to PATH
echo 'export PATH="$PATH:/workspaces/labdabbler/.devcontainer/scripts"' >> ~/.bashrc

# Final permissions fix
sudo chown -R vscode:vscode /workspaces/labdabbler

log "🎉 LabDabbler Codespace setup complete!"
log ""
log "📋 Quick Start:"
log "  1. Run 'lab-helper start' to start LabDabbler"
log "  2. Open http://localhost:5000 for the web interface"
log "  3. Use 'lab-helper deploy labs/examples/basic-srlinux-lab.clab.yml' to test"
log ""
log "🔧 Available Commands:"
log "  - lab-helper: LabDabbler management helper"
log "  - containerlab: Container lab CLI"
log "  - backend: Quick start backend"
log "  - frontend: Quick start frontend"
log ""
log "📖 Documentation:"
log "  - Containerlab: https://containerlab.dev/"
log "  - FastAPI: http://localhost:8000/docs"
log ""

# Create welcome message
cat > /workspaces/labdabbler/CODESPACE_README.md << 'EOF'
# 🚀 LabDabbler in GitHub Codespaces

Welcome to your LabDabbler development environment! This Codespace is fully configured with:

## ✅ Pre-installed Tools
- **Containerlab** - Network lab orchestrator
- **Docker-in-Docker** - Full container support
- **Python 3.11** - Backend development
- **Node.js 20** - Frontend development
- **VRNetlab support** - VM-to-container conversion
- **Git** & **GitHub CLI** - Version control

## 🚀 Quick Start

1. **Start LabDabbler:**
   ```bash
   lab-helper start
   ```

2. **Access the Web Interface:**
   - Frontend: http://localhost:5000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Deploy a Test Lab:**
   ```bash
   lab-helper deploy labs/examples/basic-srlinux-lab.clab.yml
   ```

## 🔧 Helper Commands

| Command | Description |
|---------|-------------|
| `lab-helper start` | Start LabDabbler services |
| `lab-helper stop` | Stop all services |
| `lab-helper status` | Check service status |
| `lab-helper labs` | List available labs |
| `lab-helper deploy <file>` | Deploy a lab |
| `lab-helper destroy <file>` | Destroy a lab |

## 🐳 Container Management

| Command | Description |
|---------|-------------|
| `lablist` | List all running labs |
| `labstatus` | Show container status |
| `containerlab inspect --all` | Detailed lab info |

## 📁 Project Structure

```
/workspaces/labdabbler/
├── web/
│   ├── backend/          # FastAPI backend
│   └── frontend/         # React frontend
├── labs/                 # Lab configurations
├── data/                 # Runtime data
├── configs/              # Device configurations
└── .devcontainer/        # Codespace config
```

## 🔍 Troubleshooting

**Services won't start?**
```bash
sudo service docker restart
lab-helper start
```

**Permission issues?**
```bash
sudo chown -R vscode:vscode /workspaces/labdabbler
```

**Need to see logs?**
```bash
# Backend logs
cd web/backend && python app.py

# Frontend logs  
cd web/frontend && npm run dev
```

## 🌐 Networking

This Codespace supports:
- ✅ Docker-in-Docker for containerlab
- ✅ Bridge networking for lab connectivity  
- ✅ Port forwarding for web interfaces
- ✅ Network namespaces for isolation

## 📚 Learn More

- [Containerlab Documentation](https://containerlab.dev/)
- [LabDabbler GitHub Repository](https://github.com/your-repo/labdabbler)
- [VRNetlab Documentation](https://containerlab.dev/manual/vrnetlab/)

Happy labbing! 🧪
EOF

echo "✨ Setup complete! Check CODESPACE_README.md for quick start instructions."
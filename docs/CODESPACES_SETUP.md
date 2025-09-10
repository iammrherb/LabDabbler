# 🚀 LabDabbler GitHub Codespaces Setup

This document provides comprehensive instructions for running LabDabbler in GitHub Codespaces with full containerlab and networking capabilities.

## 🏗️ Architecture Overview

The Codespaces environment includes:

- **Ubuntu 22.04 base** with Docker-in-Docker support
- **Containerlab 0.56.0** for network topology orchestration
- **Python 3.11** with FastAPI backend
- **Node.js 20** with React frontend
- **VRNetlab support** for VM-to-container conversion
- **Privileged containers** for network namespace access

## 📁 Configuration Files

| File | Purpose |
|------|---------|
| `.devcontainer/devcontainer.json` | Main Codespace configuration |
| `.devcontainer/setup.sh` | Post-create environment setup |
| `.github/codespaces/devcontainer.json` | GitHub-specific overrides |
| `.github/workflows/codespaces-prebuilds.yml` | Prebuild automation |
| `.vscode/settings.json` | VS Code workspace settings |

## 🚀 Quick Start Guide

### 1. Create a Codespace

1. Navigate to the GitHub repository
2. Click "Code" → "Codespaces" → "Create codespace on main"
3. Wait for the environment to initialize (5-10 minutes first time)

### 2. Start LabDabbler

```bash
# Using the helper script
lab-helper start

# Or manually
cd /workspaces/labdabbler
./start-labdabbler.sh
```

### 3. Access the Interface

- **Frontend**: http://localhost:5000 (opens automatically)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Deploy a Test Lab

```bash
# List available labs
lab-helper labs

# Deploy the example lab
lab-helper deploy labs/examples/basic-srlinux-lab.clab.yml

# Check status
lab-helper status
```

## 🔧 Environment Features

### Installed Tools

- **containerlab** v0.56.0 - Network topology orchestrator
- **Docker** with Docker-in-Docker support
- **yq** - YAML processor for lab files
- **Git** & **GitHub CLI** - Version control
- **uv** - Fast Python package manager
- **Go** 1.21.6 - Required for containerlab builds

### Pre-configured Aliases

```bash
# LabDabbler management
lab-helper start|stop|status|labs|deploy|destroy

# Quick navigation
cdlab      # cd /workspaces/labdabbler
cdlabs     # cd /workspaces/labdabbler/labs
cdback     # cd /workspaces/labdabbler/web/backend
cdfront    # cd /workspaces/labdabbler/web/frontend

# Docker helpers
dps        # docker ps
dimg       # docker images
dnet       # docker network ls

# Lab management
lab        # containerlab
labdeploy  # containerlab deploy
labdestroy # containerlab destroy
lablist    # containerlab inspect --all
labstatus  # formatted container status
```

### Port Forwarding

| Port | Service | Auto-Forward |
|------|---------|--------------|
| 5000 | React Frontend | ✅ Preview |
| 8000 | FastAPI Backend | 🔔 Notify |
| 80/443 | Lab Device Web UIs | Silent |
| 830 | NETCONF | Silent |
| 8080/9090 | Monitoring | Silent |

## 🐳 Container Support

### Pre-pulled Images

The setup automatically pulls commonly used images:

- `ghcr.io/nokia/srlinux:latest`
- `frrouting/frr:latest`
- `alpine:latest`
- `ubuntu:22.04`
- `nginx:latest`
- `busybox:latest`

### VRNetlab Integration

Build custom network OS containers:

```bash
# Initialize vrnetlab repository
curl -X POST http://localhost:8000/api/vrnetlab/init

# Upload VM image via web interface or API
# Build container via web interface or API
```

## 🌐 Networking Configuration

### Bridge Networking

The environment supports full bridge networking for lab connectivity:

```bash
# IP forwarding enabled
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# Bridge modules loaded
bridge
br_netfilter
```

### Docker-in-Docker

- Privileged container access
- Volume mounts for persistent Docker data
- Full container lifecycle management

## 📋 Example Lab Files

### Basic SR Linux Lab

Location: `labs/examples/basic-srlinux-lab.clab.yml`

```yaml
name: basic-srlinux-lab

topology:
  nodes:
    srl1:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd2
    srl2:
      kind: nokia_srlinux
      image: ghcr.io/nokia/srlinux:latest
      type: ixrd2

  links:
    - endpoints: ["srl1:e1-1", "srl2:e1-1"]
```

Deploy with: `lab-helper deploy labs/examples/basic-srlinux-lab.clab.yml`

## 🔍 Troubleshooting

### Common Issues

**🚫 Services won't start**
```bash
sudo service docker restart
lab-helper start
```

**🚫 Permission denied errors**
```bash
sudo chown -R vscode:vscode /workspaces/labdabbler
sudo usermod -aG docker vscode
```

**🚫 Container creation fails**
```bash
# Check Docker daemon
docker info

# Check disk space
df -h

# Restart Docker service
sudo service docker restart
```

**🚫 Lab deployment fails**
```bash
# Check containerlab version
containerlab version

# Verify lab syntax
containerlab inspect -t <lab-file>

# Check container images
docker images
```

### Log Locations

```bash
# Application logs
cd /workspaces/labdabbler/logs

# Workflow logs
tail -f /tmp/logs/*.log

# Docker logs
docker logs <container-name>

# Containerlab logs
containerlab inspect --name <lab-name>
```

### Debug Commands

```bash
# System status
lab-helper status

# Docker status
docker ps -a
docker network ls
docker volume ls

# Process status
ps aux | grep -E "(python|node|docker)"

# Network interfaces
ip addr show
ip route show
```

## 🚀 Performance Optimization

### Prebuild Strategy

Enable prebuilds for faster startup:

1. Configure `.github/workflows/codespaces-prebuilds.yml`
2. Set up repository secrets if needed
3. Monitor prebuild status in repository settings

### Resource Management

The Codespace is configured for:

- **CPU**: Optimized for concurrent containers
- **Memory**: Sufficient for multiple network nodes
- **Storage**: Docker volume persistence
- **Network**: Bridge networking with namespace isolation

## 🔐 Security Considerations

### Container Privileges

- Privileged mode required for networking
- Docker-in-Docker for container management
- Network namespace access for lab isolation

### Secret Management

- Use GitHub Codespace secrets for sensitive data
- Environment variables for API keys
- Secure VRNetlab image handling

## 📖 Additional Resources

- [Containerlab Documentation](https://containerlab.dev/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [Docker-in-Docker Best Practices](https://docs.docker.com/engine/security/)
- [VRNetlab Project](https://github.com/hellt/vrnetlab)

## 🤝 Contributing

When modifying the Codespace configuration:

1. Test changes in a new Codespace
2. Update this documentation
3. Verify all lab types work correctly
4. Check performance impact
5. Submit pull request with detailed testing notes

## 🆘 Support

For issues specific to the Codespace environment:

1. Check the troubleshooting section above
2. Review GitHub Codespace logs
3. Open an issue with environment details
4. Include relevant log outputs

---

**Happy labbing in the cloud! 🌥️🧪**
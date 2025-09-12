# LabDabbler - Master Lab Repository

## Overview

LabDabbler is a comprehensive containerlab network lab platform designed for cybersecurity testing and network automation. It serves as a centralized repository for network topologies, with a focus on Portnox security testing (802.1x/MAB, TACACS, ZTNA) and container-based network simulation. The platform provides a web-based interface for building custom labs, managing container catalogs, and launching network topologies using containerlab.

The system is designed to run in GitHub Codespaces with full containerlab support, allowing users to deploy complex network topologies directly in the cloud. It integrates with multiple container registries and GitHub repositories to provide access to a vast collection of network operating systems, security tools, and pre-built lab topologies.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**December 12, 2025:**
- ✅ **Complete GitHub Codespaces Integration**: Full export functionality for labs to GitHub Codespaces with devcontainer configuration, containerlab extension, and VSCode workspace setup
- ✅ **NetLab Automation System**: Integrated netlab for template-based lab generation with async subprocess handling
- ✅ **Security Enhancements**: Added authentication guards for sensitive endpoints and production safeguards
- ✅ **GitHub Actions Workflow**: Comprehensive CI/CD pipeline for lab validation, deployment, and health monitoring
- ✅ **Enhanced Lab Builder**: Visual drag-and-drop topology designer with real-time validation and multi-format export
- ✅ **Fixed Frontend Environment**: Converted all process.env references to import.meta.env for Vite compatibility

## System Architecture

### Frontend Architecture
The frontend is built as a React application using Vite as the build tool. It provides a modern web interface for lab management with the following components:
- **React 19.1.1** with modern hooks and functional components
- **Vite 7.1.5** for fast development and optimized builds
- **Component-based architecture** for lab builders, container catalogs, and topology management
- **GitHub Codespaces Export**: Direct export to GitHub with complete development environment setup
- **Responsive design** optimized for both development and production environments

### Backend Architecture
The backend follows a microservices-inspired architecture built with FastAPI:
- **FastAPI framework** providing RESTful APIs with automatic documentation
- **Service-oriented design** with separate services for container discovery, lab management, repository syncing, and VRNetLab integration
- **Asynchronous processing** for background tasks like repository synchronization
- **Production middleware stack** including security, performance, and monitoring layers
- **JSON file-based storage** for configuration and metadata persistence

### Container and Virtualization Strategy
The platform supports multiple approaches to network simulation:
- **Native containerized NOSes** (Nokia SR Linux, Arista cEOS, Cisco XRd, etc.)
- **VM-to-container conversion** via VRNetLab integration for traditional network OS images
- **Docker-in-Docker** architecture for running containerlab within containers
- **Privileged container execution** to support network namespace operations

### Development Environment
Optimized for GitHub Codespaces with comprehensive development tooling:
- **Ubuntu 22.04 base** with Docker-in-Docker support
- **Multi-language support** (Python 3.11, Node.js 20, Go)
- **Containerlab 0.56.0** pre-installed for network topology orchestration
- **VS Code integration** with workspace-specific settings and extensions

### Data Management
File-based data storage using JSON for simplicity and portability:
- **Repository metadata** tracking synced GitHub repositories and lab collections
- **Container catalogs** maintaining comprehensive lists of available network OS containers
- **Lab configurations** storing topology definitions and launch parameters
- **Sync status tracking** for automated repository updates

### Security Architecture
Production-ready security implementations:
- **Rate limiting** using Redis-backed sliding window algorithms
- **Input validation** and sanitization middleware
- **CORS configuration** for controlled frontend-backend communication
- **Secrets management** with encryption for sensitive configuration data
- **Security headers** implementation for production deployments

## External Dependencies

### Container Registries
- **Docker Hub** for public container images
- **GitHub Container Registry (ghcr.io)** for Nokia SR Linux and other vendor images
- **Portnox registry** for ZTNA gateway and security tools
- **Quay.io** for additional network OS containers

### GitHub Integration
- **Repository synchronization** with multiple containerlab topology collections
- **Automated lab discovery** from srl-labs/containerlab, hellt/clabs, PacketAnglers/clab-topos
- **GitHub API access** for repository cloning and content retrieval
- **Optional GitHub token** authentication for increased API rate limits

### Runtime Dependencies
- **Docker Engine** for container orchestration and networking
- **Containerlab** as the primary network topology management tool
- **VRNetLab** for VM-to-container conversion capabilities
- **Git** for repository management and synchronization

### Production Dependencies
- **Redis** for caching, rate limiting, and session management
- **Nginx** as reverse proxy with SSL termination
- **PostgreSQL** for enhanced data persistence (optional upgrade path)
- **Prometheus & Grafana** for monitoring and observability
- **Fluentd** for centralized logging

### Network Vendor Integrations
- **Nokia SR Linux** native container support
- **Arista cEOS** container integration
- **Cisco XRd** and traditional IOS images via VRNetLab
- **Juniper cRPD** and VM-based platforms
- **Open source alternatives** (FRRouting, VyOS, SONiC)

### Development Tools
- **APScheduler** for background task scheduling
- **aiohttp** for asynchronous HTTP operations
- **PyYAML** for configuration file parsing
- **Scrapli** for network device automation (optional)
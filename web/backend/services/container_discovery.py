import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ContainerDiscoveryService:
    """Service to discover and catalog containers from various registries"""
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.containers_file = self.data_dir / "containers.json"
        
    async def discover_all_containers(self) -> Dict:
        """Discover containers from all configured sources"""
        logger.info("Starting container discovery...")
        
        containers = {
            "portnox": await self.discover_portnox_containers(),
            "network_os_native": await self.discover_native_network_os_containers(),
            "network_os_vm_based": await self.discover_vm_based_network_os_containers(),
            "open_source_network": await self.discover_open_source_network_containers(),
            "security_firewalls": await self.discover_security_firewall_containers(),
            "security": await self.discover_security_containers(),
            "services": await self.discover_service_containers(),
            "last_updated": str(asyncio.get_event_loop().time())
        }
        
        # Save to file
        with open(self.containers_file, 'w') as f:
            json.dump(containers, f, indent=2)
            
        logger.info(f"Container discovery complete. Found {sum(len(v) if isinstance(v, list) else 0 for v in containers.values())} containers")
        return containers
    
    async def discover_portnox_containers(self) -> List[Dict]:
        """Discover all Portnox containers from Docker Hub"""
        portnox_containers = []
        
        # Known Portnox containers - we'll scan Docker Hub for these
        known_portnox_images = [
            "portnox/local-radius",
            "portnox/tacacs",
            "portnox/dhcp", 
            "portnox/auto-updater",
            "portnox/ztna-gateway",
            "portnox/unifi-agent",
            "portnox/siem-collector",
            "portnox/radius-authenticator",
            "portnox/network-scanner"
        ]
        
        async with aiohttp.ClientSession() as session:
            for image in known_portnox_images:
                try:
                    container_info = await self.get_dockerhub_info(session, image)
                    if container_info:
                        portnox_containers.append(container_info)
                except Exception as e:
                    logger.warning(f"Failed to get info for {image}: {e}")
                    # Add fallback info
                    portnox_containers.append({
                        "name": image.split("/")[1],
                        "image": f"{image}:latest",
                        "description": f"Portnox {image.split('/')[1].replace('-', ' ').title()}",
                        "tags": ["latest"],
                        "category": "portnox"
                    })
        
        return portnox_containers
    
    async def discover_native_network_os_containers(self) -> List[Dict]:
        """Discover native containerized network operating systems"""
        native_containers = [
            # Nokia SR Linux - Publicly available
            {
                "name": "Nokia SR Linux (Latest)",
                "image": "ghcr.io/nokia/srlinux:latest",
                "kind": "nokia_srlinux",
                "description": "Nokia SR Linux Network OS - Latest Release",
                "vendor": "Nokia",
                "category": "network_os_native",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "ghcr.io",
                "documentation": "https://learn.srlinux.dev/"
            },
            {
                "name": "Nokia SR Linux 24.10.1",
                "image": "ghcr.io/nokia/srlinux:24.10.1",
                "kind": "nokia_srlinux",
                "description": "Nokia SR Linux - ARM64 Native with Universal Support",
                "vendor": "Nokia",
                "category": "network_os_native",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "ghcr.io",
                "features": ["ARM64 native", "NETCONF enabled", "gRPC server"]
            },
            {
                "name": "Nokia SR Linux 24.7.2",
                "image": "ghcr.io/nokia/srlinux:24.7.2",
                "kind": "nokia_srlinux",
                "description": "Nokia SR Linux - Stable Release with NETCONF",
                "vendor": "Nokia",
                "category": "network_os_native",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "ghcr.io",
                "features": ["NETCONF port 830", "Enhanced security"]
            },
            # Arista cEOS - Requires registration
            {
                "name": "Arista cEOS (Latest)",
                "image": "ceos:latest",
                "kind": "arista_ceos",
                "description": "Arista Container EOS - Latest Release",
                "vendor": "Arista",
                "category": "network_os_native",
                "architecture": ["amd64"],
                "access": "registration_required",
                "registry": "arista.com (manual download)",
                "download_url": "https://www.arista.com/en/support/software-download",
                "requirements": "Arista.com account required",
                "installation_notes": "Download tar.xz file and import with docker load"
            },
            {
                "name": "Arista cEOS 4.32.0F",
                "image": "ceos:4.32.0F",
                "kind": "arista_ceos",
                "description": "Arista Container EOS - Stable 4.32.0F",
                "vendor": "Arista",
                "category": "network_os_native",
                "architecture": ["amd64"],
                "access": "registration_required",
                "registry": "arista.com (manual download)"
            },
            # Cisco XRd - Requires CCO access
            {
                "name": "Cisco XRd Control Plane",
                "image": "localhost/ios-xr:latest",
                "kind": "cisco_xrd",
                "description": "Cisco XRd Control Plane Router",
                "vendor": "Cisco",
                "category": "network_os_native",
                "architecture": ["amd64"],
                "access": "cco_required",
                "registry": "software.cisco.com (manual download)",
                "requirements": "Active Cisco service contract required",
                "installation_notes": "Download from CCO and docker load locally"
            },
            {
                "name": "Cisco XRd vRouter",
                "image": "localhost/xrd-vrouter:latest",
                "kind": "cisco_xrd",
                "description": "Cisco XRd vRouter with Data Plane",
                "vendor": "Cisco",
                "category": "network_os_native",
                "architecture": ["amd64"],
                "access": "cco_required",
                "registry": "software.cisco.com (manual download)"
            },
            # Juniper cRPD - Enterprise registry
            {
                "name": "Juniper cRPD Latest",
                "image": "enterprise-hub.juniper.net:443/crpd-docker-prod/crpd:latest",
                "kind": "juniper_crpd",
                "description": "Juniper Containerized Routing Protocol Daemon",
                "vendor": "Juniper",
                "category": "network_os_native",
                "architecture": ["amd64", "arm64"],
                "access": "enterprise_required",
                "registry": "enterprise-hub.juniper.net",
                "requirements": "Juniper enterprise account required",
                "features": ["Full Junos CLI", "BGP/OSPF/ISIS support", "ARM64 support"]
            },
            {
                "name": "Juniper cRPD 24.2R1.14",
                "image": "enterprise-hub.juniper.net:443/crpd-docker-prod/crpd:24.2R1.14",
                "kind": "juniper_crpd",
                "description": "Juniper cRPD - Stable 24.2R1.14 Release",
                "vendor": "Juniper",
                "category": "network_os_native",
                "architecture": ["amd64", "arm64"],
                "access": "enterprise_required",
                "registry": "enterprise-hub.juniper.net"
            }
        ]
        
        return native_containers
    
    async def discover_vm_based_network_os_containers(self) -> List[Dict]:
        """Discover VM-based network OS containers (using vrnetlab/hellt)"""
        vm_based_containers = [
            # Nokia
            {
                "name": "Nokia SR-OS (vSIM)",
                "image": "vrnetlab/vr-sros:latest",
                "kind": "nokia_sros",
                "description": "Nokia SR-OS Virtual SIM - VM-based",
                "vendor": "Nokia",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab",
                "requirements": "Nokia SR-OS qcow2 image required",
                "build_info": "Use hellt/vrnetlab project to build"
            },
            # Juniper VM-based
            {
                "name": "Juniper vMX",
                "image": "vrnetlab/vr-vmx:latest",
                "kind": "juniper_vmx", 
                "description": "Juniper vMX Router - VM-based",
                "vendor": "Juniper",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            {
                "name": "Juniper vQFX",
                "image": "vrnetlab/vr-vqfx:latest",
                "kind": "juniper_vqfx",
                "description": "Juniper vQFX Switch - VM-based",
                "vendor": "Juniper",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            {
                "name": "Juniper vSRX",
                "image": "vrnetlab/vr-vsrx:latest",
                "kind": "juniper_vsrx",
                "description": "Juniper vSRX Firewall - VM-based",
                "vendor": "Juniper",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # Cisco VM-based
            {
                "name": "Cisco IOS XRv9k",
                "image": "vrnetlab/vr-xrv9k:latest",
                "kind": "cisco_xrv9k",
                "description": "Cisco IOS XRv9000 - VM-based",
                "vendor": "Cisco",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            {
                "name": "Cisco Nexus 9000v",
                "image": "vrnetlab/vr-n9kv:latest",
                "kind": "cisco_n9kv",
                "description": "Cisco Nexus 9000v Switch - VM-based",
                "vendor": "Cisco",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            {
                "name": "Cisco CSR 1000v",
                "image": "vrnetlab/vr-csr:latest",
                "kind": "cisco_csr1000v",
                "description": "Cisco CSR 1000v Router - VM-based",
                "vendor": "Cisco",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # Arista VM-based
            {
                "name": "Arista vEOS",
                "image": "vrnetlab/vr-veos:latest",
                "kind": "arista_veos",
                "description": "Arista vEOS Switch - VM-based",
                "vendor": "Arista",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # MikroTik (Pre-built available)
            {
                "name": "MikroTik RouterOS CHR (Stable)",
                "image": "docker.io/iparchitechs/chr:stable",
                "kind": "mikrotik_ros",
                "description": "MikroTik RouterOS CHR - Stable Release",
                "vendor": "MikroTik",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/iparchitechs",
                "features": ["Pre-built images", "Multiple versions available"]
            },
            {
                "name": "MikroTik RouterOS CHR (Long-term)",
                "image": "docker.io/iparchitechs/chr:long-term",
                "kind": "mikrotik_ros",
                "description": "MikroTik RouterOS CHR - Long-term Support",
                "vendor": "MikroTik",
                "category": "network_os_vm_based",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/iparchitechs"
            }
        ]
        
        return vm_based_containers
    
    async def discover_open_source_network_containers(self) -> List[Dict]:
        """Discover open source network operating systems"""
        open_source_containers = [
            # FRR - Free Range Routing
            {
                "name": "FRRouting (Latest)",
                "image": "frrouting/frr:latest",
                "kind": "linux",
                "description": "FRRouting Protocol Suite - Latest",
                "vendor": "FRRouting Project",
                "category": "open_source_network",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/frrouting",
                "protocols": ["BGP", "OSPF", "ISIS", "RIP", "EIGRP", "PIM"],
                "documentation": "https://docs.frrouting.org/"
            },
            {
                "name": "FRRouting 10.1",
                "image": "frrouting/frr:v10.1.0",
                "kind": "linux",
                "description": "FRRouting 10.1 - Stable Release",
                "vendor": "FRRouting Project",
                "category": "open_source_network",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/frrouting"
            },
            # VyOS
            {
                "name": "VyOS Rolling",
                "image": "vyos/vyos:1.4-rolling",
                "kind": "vyos",
                "description": "VyOS Router - Rolling Release",
                "vendor": "VyOS",
                "category": "open_source_network",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/vyos",
                "features": ["Linux-based", "Enterprise features", "CLI similar to Vyatta"]
            },
            {
                "name": "VyOS 1.4 LTS",
                "image": "vyos/vyos:1.4-lts",
                "kind": "vyos",
                "description": "VyOS Router - Long Term Support",
                "vendor": "VyOS",
                "category": "open_source_network",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/vyos"
            },
            # SONiC - Microsoft's containerized network OS
            {
                "name": "SONiC Virtual Switch",
                "image": "docker-sonic-vs:latest",
                "kind": "sonic-vs",
                "description": "Microsoft SONiC - Virtual Switch Container",
                "vendor": "Microsoft/SONiC",
                "category": "open_source_network",
                "architecture": ["amd64", "arm64"],
                "access": "build_required",
                "registry": "Build from Azure Pipeline",
                "requirements": "Download from sonic-build.azurewebsites.net",
                "features": ["Cloud-scale networking", "Redis-based state", "Modular containers"]
            },
            # OpenWRT
            {
                "name": "OpenWrt Latest",
                "image": "openwrt/rootfs:latest",
                "kind": "linux",
                "description": "OpenWrt Router OS - Container Rootfs",
                "vendor": "OpenWrt Project",
                "category": "open_source_network",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/openwrt",
                "features": ["Lightweight", "Embedded router OS", "Package management"]
            }
        ]
        
        return open_source_containers
    
    async def discover_security_firewall_containers(self) -> List[Dict]:
        """Discover security appliance and firewall containers"""
        firewall_containers = [
            # Fortinet FortiGate
            {
                "name": "Fortinet FortiGate VM (Latest)",
                "image": "vrnetlab/vr-fortios:latest",
                "kind": "fortinet_fortigate",
                "description": "Fortinet FortiGate Firewall - VM-based",
                "vendor": "Fortinet",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab",
                "requirements": "FortiOS qcow2 image from Fortinet support",
                "build_info": "Requires FortiGate VM license for full functionality",
                "ports": ["80:80", "443:443"]
            },
            {
                "name": "Fortinet FortiGate 7.0.14",
                "image": "vrnetlab/vr-fortios:7.0.14",
                "kind": "fortinet_fortigate",
                "description": "Fortinet FortiGate 7.0.14 - Tested Version",
                "vendor": "Fortinet",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # Palo Alto PAN-OS
            {
                "name": "Palo Alto PAN-OS (Latest)",
                "image": "vrnetlab/vr-pan:latest",
                "kind": "paloalto_panos",
                "description": "Palo Alto PAN-OS Firewall - VM-based",
                "vendor": "Palo Alto Networks",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab",
                "requirements": "PAN-OS qcow2 image from Palo Alto support portal",
                "features": ["Web UI on port 443", "SSH access", "API support"]
            },
            {
                "name": "Palo Alto PAN-OS 10.2.6",
                "image": "vrnetlab/vr-pan:10.2.6",
                "kind": "paloalto_panos",
                "description": "Palo Alto PAN-OS 10.2.6 - Stable Release",
                "vendor": "Palo Alto Networks",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # Check Point
            {
                "name": "Check Point CloudGuard",
                "image": "vrnetlab/vr-checkpoint:latest",
                "kind": "checkpoint_cloudguard",
                "description": "Check Point CloudGuard Security Gateway",
                "vendor": "Check Point",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "build_required",
                "registry": "Build with hellt/vrnetlab"
            },
            # pfSense (Community)
            {
                "name": "pfSense",
                "image": "pfsense/pfsense:latest",
                "kind": "generic_vm",
                "description": "pfSense Firewall - Open Source",
                "vendor": "Netgate/pfSense",
                "category": "security_firewalls",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/pfsense",
                "features": ["Open source", "Web interface", "VPN support"]
            }
        ]
        
        return firewall_containers
    
    async def discover_security_containers(self) -> List[Dict]:
        """Discover security and penetration testing containers"""
        security_containers = [
            {
                "name": "kali-linux",
                "image": "kalilinux/kali-rolling:latest",
                "description": "Kali Linux Penetration Testing",
                "category": "security"
            },
            {
                "name": "metasploit",
                "image": "metasploitframework/metasploit-framework:latest",
                "description": "Metasploit Framework",
                "category": "security"
            },
            {
                "name": "nmap",
                "image": "instrumentisto/nmap:latest",
                "description": "Network Discovery and Security Auditing",
                "category": "security"
            },
            {
                "name": "wireshark", 
                "image": "linuxserver/wireshark:latest",
                "description": "Network Protocol Analyzer",
                "ports": ["3000:3000"],
                "category": "security"
            }
        ]
        
        return security_containers
    
    async def discover_service_containers(self) -> List[Dict]:
        """Discover network service containers"""
        service_containers = [
            {
                "name": "FreeRADIUS Server",
                "image": "freeradius/freeradius-server:latest",
                "description": "FreeRADIUS Authentication Server",
                "ports": ["1812:1812/udp", "1813:1813/udp"],
                "category": "services",
                "protocols": ["RADIUS", "802.1X", "EAP"],
                "access": "public",
                "registry": "docker.io/freeradius"
            },
            {
                "name": "BIND9 DNS Server",
                "image": "internetsystemsconsortium/bind9:latest", 
                "description": "BIND9 DNS Server - Internet Systems Consortium",
                "ports": ["53:53/tcp", "53:53/udp"],
                "category": "services",
                "protocols": ["DNS", "DNSSEC"],
                "access": "public",
                "registry": "docker.io/internetsystemsconsortium"
            },
            {
                "name": "ISC DHCP Server",
                "image": "networkboot/dhcpd:latest",
                "description": "ISC DHCP Server for Network Boot",
                "category": "services",
                "protocols": ["DHCP", "BOOTP"],
                "access": "public",
                "registry": "docker.io/networkboot"
            },
            {
                "name": "TACACS+ Server",
                "image": "dchidell/docker-tacacs:latest",
                "description": "TACACS+ Authentication Server",
                "ports": ["49:49/tcp"],
                "category": "services",
                "protocols": ["TACACS+"],
                "access": "public",
                "registry": "docker.io/dchidell"
            },
            {
                "name": "TFTP Server",
                "image": "pghalliday/tftp:latest",
                "description": "TFTP Server for Network Devices",
                "ports": ["69:69/udp"],
                "category": "services",
                "protocols": ["TFTP"],
                "access": "public",
                "registry": "docker.io/pghalliday"
            },
            {
                "name": "NTP Server",
                "image": "cturra/ntp:latest",
                "description": "Network Time Protocol Server",
                "ports": ["123:123/udp"],
                "category": "services",
                "protocols": ["NTP"],
                "access": "public",
                "registry": "docker.io/cturra"
            }
        ]
        
        return service_containers
    
    async def get_dockerhub_info(self, session: aiohttp.ClientSession, image: str) -> Optional[Dict]:
        """Get container information from Docker Hub API"""
        try:
            if "/" in image:
                namespace, repo = image.split("/", 1)
            else:
                namespace, repo = "library", image
                
            url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get tags
                    tags_url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/tags/"
                    async with session.get(tags_url) as tags_response:
                        tags_data = await tags_response.json() if tags_response.status == 200 else {}
                        tags = [tag["name"] for tag in tags_data.get("results", [])][:10]  # First 10 tags
                    
                    return {
                        "name": repo,
                        "image": f"{namespace}/{repo}:latest",
                        "description": data.get("description", f"{namespace}/{repo} container"),
                        "tags": tags or ["latest"],
                        "pull_count": data.get("pull_count", 0),
                        "star_count": data.get("star_count", 0),
                        "last_updated": data.get("last_updated"),
                        "category": "external"
                    }
        except Exception as e:
            logger.error(f"Error fetching Docker Hub info for {image}: {e}")
            return None
    
    def load_containers(self) -> Dict:
        """Load containers from file"""
        if self.containers_file.exists():
            with open(self.containers_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def refresh_containers(self) -> Dict:
        """Refresh container discovery"""
        return await self.discover_all_containers()
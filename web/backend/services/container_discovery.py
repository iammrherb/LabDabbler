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
            "security_pentesting": await self.discover_pentesting_containers(),
            "security_monitoring": await self.discover_security_monitoring_containers(),
            "services": await self.discover_service_containers(),
            "network_simulation": await self.discover_network_simulation_containers(),
            "network_monitoring": await self.discover_network_monitoring_containers(),
            "network_automation": await self.discover_network_automation_containers(),
            "development": await self.discover_development_containers(),
            "ci_cd": await self.discover_ci_cd_containers(),
            "databases": await self.discover_database_containers(),
            "message_queues": await self.discover_message_queue_containers(),
            "web_servers": await self.discover_web_server_containers(),
            "monitoring_observability": await self.discover_monitoring_containers(),
            "analytics": await self.discover_analytics_containers(),
            "testing_load": await self.discover_testing_containers(),
            "vrnetlab_built": await self.discover_vrnetlab_built_containers(),
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
    
    async def discover_pentesting_containers(self) -> List[Dict]:
        """Discover penetration testing and offensive security containers"""
        pentesting_containers = [
            {
                "name": "Kali Linux",
                "image": "kalilinux/kali-rolling:latest",
                "kind": "linux",
                "description": "Complete penetration testing platform with 600+ tools",
                "vendor": "Kali Linux",
                "category": "security_pentesting",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/kalilinux",
                "ports": ["22:22", "80:80", "443:443"],
                "tools": ["nmap", "metasploit", "burpsuite", "wireshark", "aircrack-ng"],
                "documentation": "https://www.kali.org/docs/containers/"
            },
            {
                "name": "Metasploit Framework",
                "image": "metasploitframework/metasploit-framework:latest",
                "kind": "linux",
                "description": "World's most used penetration testing framework",
                "vendor": "Rapid7",
                "category": "security_pentesting",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/metasploitframework",
                "ports": ["4444:4444", "8080:8080"],
                "features": ["Exploit development", "Payload generation", "Post-exploitation"]
            },
            {
                "name": "OWASP ZAP",
                "image": "ghcr.io/zaproxy/zaproxy:stable",
                "kind": "linux",
                "description": "OWASP Zed Attack Proxy - Web application security scanner",
                "vendor": "OWASP",
                "category": "security_pentesting",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "ghcr.io/zaproxy",
                "ports": ["8080:8080"],
                "features": ["Web app scanning", "API security testing", "Proxy functionality"]
            },
            {
                "name": "Burp Suite Community",
                "image": "portswigger/burp-suite:latest",
                "kind": "linux",
                "description": "Web application security testing platform",
                "vendor": "PortSwigger",
                "category": "security_pentesting",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/portswigger",
                "ports": ["8080:8080"]
            },
            {
                "name": "Nmap",
                "image": "instrumentisto/nmap:latest",
                "kind": "linux",
                "description": "Network discovery and security auditing utility",
                "vendor": "Nmap Project",
                "category": "security_pentesting",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/instrumentisto",
                "features": ["Port scanning", "OS detection", "Service enumeration"]
            },
            {
                "name": "Nikto",
                "image": "sullo/nikto:latest",
                "kind": "linux",
                "description": "Web server scanner for vulnerabilities",
                "vendor": "CIRT.net",
                "category": "security_pentesting",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/sullo"
            },
            {
                "name": "SQLmap",
                "image": "paoloo/sqlmap:latest",
                "kind": "linux",
                "description": "Automatic SQL injection and database takeover tool",
                "vendor": "SQLmap Project",
                "category": "security_pentesting",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/paoloo"
            },
            {
                "name": "Nuclei",
                "image": "projectdiscovery/nuclei:latest",
                "kind": "linux",
                "description": "Fast and customisable vulnerability scanner",
                "vendor": "ProjectDiscovery",
                "category": "security_pentesting",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/projectdiscovery",
                "features": ["Template-based scanning", "YAML templates", "Community templates"]
            }
        ]
        return pentesting_containers
    
    async def discover_security_monitoring_containers(self) -> List[Dict]:
        """Discover security monitoring and SIEM containers"""
        security_monitoring_containers = [
            {
                "name": "Wazuh",
                "image": "wazuh/wazuh-odfe:latest",
                "kind": "linux",
                "description": "Open source security platform for threat detection and response",
                "vendor": "Wazuh",
                "category": "security_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/wazuh",
                "ports": ["1514:1514/udp", "1515:1515", "55000:55000"],
                "features": ["SIEM", "HIDS", "Compliance monitoring", "Threat intelligence"]
            },
            {
                "name": "OSSEC HIDS",
                "image": "atomicorp/ossec-docker:latest",
                "kind": "linux",
                "description": "Host-based intrusion detection system",
                "vendor": "Atomicorp",
                "category": "security_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/atomicorp",
                "ports": ["1514:1514/udp"]
            },
            {
                "name": "Suricata",
                "image": "jasonish/suricata:latest",
                "kind": "linux",
                "description": "Network threat detection engine and IDS/IPS",
                "vendor": "OISF",
                "category": "security_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/jasonish",
                "features": ["IDS/IPS", "Network monitoring", "File extraction"]
            },
            {
                "name": "Zeek (Bro)",
                "image": "blacktop/zeek:latest",
                "kind": "linux",
                "description": "Network analysis framework for security monitoring",
                "vendor": "Zeek Project",
                "category": "security_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/blacktop",
                "features": ["Network analysis", "Log generation", "Protocol parsing"]
            },
            {
                "name": "Security Onion",
                "image": "securityonionsolutions/securityonion:latest",
                "kind": "linux",
                "description": "Free and open platform for threat hunting and security monitoring",
                "vendor": "Security Onion Solutions",
                "category": "security_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/securityonionsolutions",
                "ports": ["443:443", "7037:7037"],
                "features": ["Full packet capture", "Network monitoring", "Log analysis"]
            },
            {
                "name": "Fail2ban",
                "image": "lscr.io/linuxserver/fail2ban:latest",
                "kind": "linux",
                "description": "Intrusion prevention system that protects against brute-force attacks",
                "vendor": "LinuxServer.io",
                "category": "security_monitoring",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "lscr.io/linuxserver"
            }
        ]
        return security_monitoring_containers

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
        
    async def discover_network_simulation_containers(self) -> List[Dict]:
        """Discover network simulation and testing containers"""
        simulation_containers = [
            {
                "name": "GNS3 Server",
                "image": "gns3/gns3server:latest",
                "kind": "linux",
                "description": "GNS3 network simulation server",
                "vendor": "GNS3 Technologies",
                "category": "network_simulation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/gns3",
                "ports": ["3080:3080"],
                "features": ["Network emulation", "Multi-vendor support", "Topology building"]
            },
            {
                "name": "Eve-NG Community",
                "image": "eve-ng/eve-ng:latest",
                "kind": "linux",
                "description": "Emulated Virtual Environment for network simulation",
                "vendor": "Eve-NG",
                "category": "network_simulation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/eve-ng",
                "ports": ["80:80", "443:443"]
            },
            {
                "name": "CORE Network Emulator",
                "image": "coreemu/core:latest",
                "kind": "linux",
                "description": "Common Open Research Emulator for network scenarios",
                "vendor": "Boeing",
                "category": "network_simulation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/coreemu",
                "features": ["Wireless simulation", "SDN support", "Real-time emulation"]
            },
            {
                "name": "Mininet",
                "image": "iwaseyusuke/mininet:latest",
                "kind": "linux",
                "description": "Network emulator for rapid prototyping",
                "vendor": "Stanford University",
                "category": "network_simulation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/iwaseyusuke",
                "features": ["SDN testing", "OpenFlow support", "Python API"]
            },
            {
                "name": "iPerf3",
                "image": "networkstatic/iperf3:latest",
                "kind": "linux",
                "description": "Network bandwidth measurement tool",
                "vendor": "ESnet",
                "category": "network_simulation",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/networkstatic",
                "ports": ["5201:5201"],
                "features": ["Throughput testing", "TCP/UDP support", "Multiple streams"]
            },
            {
                "name": "Ostinato",
                "image": "pstavirs/ostinato:latest",
                "kind": "linux",
                "description": "Packet generator and network traffic analyzer",
                "vendor": "Ostinato",
                "category": "network_simulation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/pstavirs",
                "features": ["Traffic generation", "Protocol crafting", "Multi-stream"]
            }
        ]
        return simulation_containers
        
    async def discover_network_monitoring_containers(self) -> List[Dict]:
        """Discover network monitoring and analysis containers"""
        monitoring_containers = [
            {
                "name": "Wireshark",
                "image": "lscr.io/linuxserver/wireshark:latest",
                "kind": "linux",
                "description": "Network protocol analyzer with web interface",
                "vendor": "Wireshark Foundation",
                "category": "network_monitoring",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "lscr.io/linuxserver",
                "ports": ["3000:3000"],
                "features": ["Packet capture", "Protocol analysis", "Web interface"]
            },
            {
                "name": "Cacti",
                "image": "smcline06/cacti:latest",
                "kind": "linux",
                "description": "Complete network graphing solution using RRDTool",
                "vendor": "Cacti Group",
                "category": "network_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/smcline06",
                "ports": ["80:80", "443:443"],
                "features": ["SNMP monitoring", "Graph generation", "Threshold alerts"]
            },
            {
                "name": "LibreNMS",
                "image": "librenms/librenms:latest",
                "kind": "linux",
                "description": "Auto-discovering network monitoring system",
                "vendor": "LibreNMS Community",
                "category": "network_monitoring",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/librenms",
                "ports": ["8000:8000"],
                "features": ["Auto-discovery", "SNMP monitoring", "Alerting", "API access"]
            },
            {
                "name": "Nagios",
                "image": "jasonrivers/nagios:latest",
                "kind": "linux",
                "description": "Network and infrastructure monitoring system",
                "vendor": "Nagios Enterprises",
                "category": "network_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/jasonrivers",
                "ports": ["80:80"],
                "features": ["Host monitoring", "Service checks", "Notifications"]
            },
            {
                "name": "Zabbix Server",
                "image": "zabbix/zabbix-server-mysql:latest",
                "kind": "linux",
                "description": "Enterprise-class monitoring solution",
                "vendor": "Zabbix",
                "category": "network_monitoring",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/zabbix",
                "ports": ["10051:10051"],
                "features": ["SNMP monitoring", "Web interface", "Distributed monitoring"]
            },
            {
                "name": "PRTG Core Server",
                "image": "paessler/prtg-core-server:latest",
                "kind": "linux",
                "description": "Paessler PRTG Core Server for infrastructure monitoring",
                "vendor": "Paessler AG",
                "category": "network_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/paessler",
                "ports": ["443:443", "8080:8080"]
            },
            {
                "name": "ntopng",
                "image": "ntop/ntopng:latest",
                "kind": "linux",
                "description": "High-speed web-based network traffic monitoring",
                "vendor": "ntop",
                "category": "network_monitoring",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/ntop",
                "ports": ["3000:3000"],
                "features": ["Real-time monitoring", "DPI analysis", "Flow collection"]
            }
        ]
        return monitoring_containers
        
    async def discover_network_automation_containers(self) -> List[Dict]:
        """Discover network automation and orchestration containers"""
        automation_containers = [
            {
                "name": "Ansible",
                "image": "quay.io/ansible/ansible-runner:latest",
                "kind": "linux",
                "description": "Automation platform for configuration management",
                "vendor": "Red Hat",
                "category": "network_automation",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "quay.io/ansible",
                "features": ["Agentless", "YAML playbooks", "Network modules"]
            },
            {
                "name": "AWX (Ansible Tower)",
                "image": "quay.io/ansible/awx:latest",
                "kind": "linux",
                "description": "Web-based interface for Ansible automation",
                "vendor": "Red Hat",
                "category": "network_automation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "quay.io/ansible",
                "ports": ["8080:8080"],
                "features": ["Web UI", "Job scheduling", "RBAC", "REST API"]
            },
            {
                "name": "Netbox",
                "image": "netboxcommunity/netbox:latest",
                "kind": "linux",
                "description": "Network documentation and management tool",
                "vendor": "NetBox Community",
                "category": "network_automation",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/netboxcommunity",
                "ports": ["8080:8080"],
                "features": ["DCIM", "IPAM", "Circuits", "REST API"]
            },
            {
                "name": "Napalm",
                "image": "napalm/base:latest",
                "kind": "linux",
                "description": "Network Automation and Programmability Abstraction Layer with Multivendor support",
                "vendor": "NAPALM Community",
                "category": "network_automation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/napalm",
                "features": ["Multi-vendor support", "Configuration management", "Python library"]
            },
            {
                "name": "Nornir",
                "image": "nornir/nornir:latest",
                "kind": "linux",
                "description": "Python automation framework with threading and inventory",
                "vendor": "Nornir Community",
                "category": "network_automation",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/nornir",
                "features": ["Threading support", "Inventory management", "Plugin system"]
            },
            {
                "name": "SaltStack",
                "image": "saltstack/salt-master:latest",
                "kind": "linux",
                "description": "Event-driven automation and configuration management",
                "vendor": "VMware",
                "category": "network_automation",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/saltstack",
                "ports": ["4505:4505", "4506:4506"],
                "features": ["Event-driven", "Remote execution", "Configuration management"]
            }
        ]
        return automation_containers
    
    async def discover_development_containers(self) -> List[Dict]:
        """Discover development environment containers"""
        development_containers = [
            {
                "name": "VS Code Server",
                "image": "lscr.io/linuxserver/code-server:latest",
                "kind": "linux",
                "description": "VS Code running on a remote server, accessible through browser",
                "vendor": "LinuxServer.io",
                "category": "development",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "lscr.io/linuxserver",
                "ports": ["8443:8443"],
                "features": ["Web-based IDE", "Extension support", "Terminal access"]
            },
            {
                "name": "Jupyter Notebook",
                "image": "jupyter/base-notebook:latest",
                "kind": "linux",
                "description": "Jupyter notebook server for data science and development",
                "vendor": "Jupyter Project",
                "category": "development",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/jupyter",
                "ports": ["8888:8888"],
                "features": ["Python notebooks", "Data visualization", "Interactive computing"]
            },
            {
                "name": "GitLab CE",
                "image": "gitlab/gitlab-ce:latest",
                "kind": "linux",
                "description": "Complete DevOps platform with Git repository management",
                "vendor": "GitLab",
                "category": "development",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/gitlab",
                "ports": ["80:80", "443:443", "22:22"],
                "features": ["Git repositories", "CI/CD pipelines", "Issue tracking"]
            },
            {
                "name": "Gitea",
                "image": "gitea/gitea:latest",
                "kind": "linux",
                "description": "Lightweight Git service with web interface",
                "vendor": "Gitea",
                "category": "development",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/gitea",
                "ports": ["3000:3000", "2222:22"],
                "features": ["Git hosting", "Issue tracking", "Pull requests"]
            },
            {
                "name": "Portainer",
                "image": "portainer/portainer-ce:latest",
                "kind": "linux",
                "description": "Container management platform with web UI",
                "vendor": "Portainer",
                "category": "development",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/portainer",
                "ports": ["9000:9000"],
                "features": ["Container management", "Stack deployment", "Registry management"]
            }
        ]
        return development_containers
        
    async def discover_ci_cd_containers(self) -> List[Dict]:
        """Discover CI/CD and build automation containers"""
        ci_cd_containers = [
            {
                "name": "Jenkins",
                "image": "jenkins/jenkins:lts",
                "kind": "linux",
                "description": "Leading open-source automation server",
                "vendor": "Jenkins Community",
                "category": "ci_cd",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/jenkins",
                "ports": ["8080:8080", "50000:50000"],
                "features": ["Pipeline as code", "Plugin ecosystem", "Distributed builds"]
            },
            {
                "name": "GitLab Runner",
                "image": "gitlab/gitlab-runner:latest",
                "kind": "linux",
                "description": "GitLab CI/CD job execution agent",
                "vendor": "GitLab",
                "category": "ci_cd",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/gitlab",
                "features": ["Docker executor", "Kubernetes support", "Auto-scaling"]
            },
            {
                "name": "Drone CI",
                "image": "drone/drone:latest",
                "kind": "linux",
                "description": "Container-native continuous delivery platform",
                "vendor": "Drone.io",
                "category": "ci_cd",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/drone",
                "ports": ["80:80", "443:443"],
                "features": ["YAML pipelines", "Matrix builds", "Plugin system"]
            },
            {
                "name": "TeamCity",
                "image": "jetbrains/teamcity-server:latest",
                "kind": "linux",
                "description": "JetBrains professional CI/CD solution",
                "vendor": "JetBrains",
                "category": "ci_cd",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/jetbrains",
                "ports": ["8111:8111"],
                "features": ["Build chains", "Test reporting", "Cloud agents"]
            },
            {
                "name": "Buildkite Agent",
                "image": "buildkite/agent:latest",
                "kind": "linux",
                "description": "Buildkite build agent for CI/CD pipelines",
                "vendor": "Buildkite",
                "category": "ci_cd",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/buildkite",
                "features": ["Parallel builds", "Artifact management", "Dynamic scaling"]
            }
        ]
        return ci_cd_containers
        
    async def discover_database_containers(self) -> List[Dict]:
        """Discover database containers"""
        database_containers = [
            {
                "name": "PostgreSQL",
                "image": "postgres:latest",
                "kind": "linux",
                "description": "Advanced open-source relational database",
                "vendor": "PostgreSQL Global Development Group",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/postgres",
                "ports": ["5432:5432"],
                "features": ["ACID compliance", "JSON support", "Full-text search"]
            },
            {
                "name": "MySQL",
                "image": "mysql:latest",
                "kind": "linux",
                "description": "Popular open-source relational database",
                "vendor": "Oracle",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/mysql",
                "ports": ["3306:3306"],
                "features": ["High performance", "Replication", "Clustering"]
            },
            {
                "name": "MongoDB",
                "image": "mongo:latest",
                "kind": "linux",
                "description": "Document-oriented NoSQL database",
                "vendor": "MongoDB Inc.",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/mongo",
                "ports": ["27017:27017"],
                "features": ["Document storage", "Horizontal scaling", "Rich queries"]
            },
            {
                "name": "Redis",
                "image": "redis:latest",
                "kind": "linux",
                "description": "In-memory data structure store and cache",
                "vendor": "Redis Labs",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/redis",
                "ports": ["6379:6379"],
                "features": ["In-memory storage", "Pub/sub", "Lua scripting"]
            },
            {
                "name": "InfluxDB",
                "image": "influxdb:latest",
                "kind": "linux",
                "description": "Time series database for IoT and monitoring",
                "vendor": "InfluxData",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/influxdb",
                "ports": ["8086:8086"],
                "features": ["Time series optimization", "SQL-like queries", "Retention policies"]
            },
            {
                "name": "Elasticsearch",
                "image": "elasticsearch:8.11.0",
                "kind": "linux",
                "description": "Distributed search and analytics engine",
                "vendor": "Elastic",
                "category": "databases",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.elastic.co/elasticsearch",
                "ports": ["9200:9200", "9300:9300"],
                "features": ["Full-text search", "Real-time analytics", "RESTful API"]
            }
        ]
        return database_containers
        
    async def discover_message_queue_containers(self) -> List[Dict]:
        """Discover message queue and streaming containers"""
        queue_containers = [
            {
                "name": "RabbitMQ",
                "image": "rabbitmq:management",
                "kind": "linux",
                "description": "Feature-rich message broker with management UI",
                "vendor": "VMware",
                "category": "message_queues",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/rabbitmq",
                "ports": ["5672:5672", "15672:15672"],
                "features": ["AMQP protocol", "Management UI", "Clustering"]
            },
            {
                "name": "Apache Kafka",
                "image": "confluentinc/cp-kafka:latest",
                "kind": "linux",
                "description": "Distributed event streaming platform",
                "vendor": "Confluent",
                "category": "message_queues",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/confluentinc",
                "ports": ["9092:9092"],
                "features": ["High throughput", "Fault tolerance", "Stream processing"]
            },
            {
                "name": "Apache Pulsar",
                "image": "apachepulsar/pulsar:latest",
                "kind": "linux",
                "description": "Cloud-native distributed messaging and streaming",
                "vendor": "Apache Software Foundation",
                "category": "message_queues",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/apachepulsar",
                "ports": ["8080:8080", "6650:6650"],
                "features": ["Multi-tenancy", "Geo-replication", "Schema registry"]
            },
            {
                "name": "NATS",
                "image": "nats:latest",
                "kind": "linux",
                "description": "High-performance cloud native messaging system",
                "vendor": "NATS.io",
                "category": "message_queues",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/nats",
                "ports": ["4222:4222", "8222:8222"],
                "features": ["Lightweight", "Request-reply", "Streaming"]
            }
        ]
        return queue_containers
        
    async def discover_web_server_containers(self) -> List[Dict]:
        """Discover web server and proxy containers"""
        web_containers = [
            {
                "name": "Nginx",
                "image": "nginx:latest",
                "kind": "linux",
                "description": "High-performance web server and reverse proxy",
                "vendor": "Nginx Inc.",
                "category": "web_servers",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/nginx",
                "ports": ["80:80", "443:443"],
                "features": ["Reverse proxy", "Load balancing", "SSL termination"]
            },
            {
                "name": "Apache HTTP Server",
                "image": "httpd:latest",
                "kind": "linux",
                "description": "World's most used web server software",
                "vendor": "Apache Software Foundation",
                "category": "web_servers",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/httpd",
                "ports": ["80:80"],
                "features": ["Modular architecture", ".htaccess support", "Virtual hosts"]
            },
            {
                "name": "Traefik",
                "image": "traefik:latest",
                "kind": "linux",
                "description": "Modern reverse proxy with automatic service discovery",
                "vendor": "Traefik Labs",
                "category": "web_servers",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/traefik",
                "ports": ["80:80", "443:443", "8080:8080"],
                "features": ["Auto SSL", "Service discovery", "Load balancing"]
            },
            {
                "name": "HAProxy",
                "image": "haproxy:latest",
                "kind": "linux",
                "description": "Reliable, high-performance load balancer",
                "vendor": "HAProxy Technologies",
                "category": "web_servers",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/_/haproxy",
                "ports": ["80:80", "443:443"],
                "features": ["Load balancing", "Health checks", "Statistics"]
            }
        ]
        return web_containers
        
    async def discover_monitoring_containers(self) -> List[Dict]:
        """Discover monitoring and observability containers"""
        monitoring_containers = [
            {
                "name": "Prometheus",
                "image": "prom/prometheus:latest",
                "kind": "linux",
                "description": "Monitoring system and time series database",
                "vendor": "Prometheus Community",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/prom",
                "ports": ["9090:9090"],
                "features": ["Time series DB", "PromQL queries", "Alerting"]
            },
            {
                "name": "Grafana",
                "image": "grafana/grafana:latest",
                "kind": "linux",
                "description": "Analytics and interactive visualization platform",
                "vendor": "Grafana Labs",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/grafana",
                "ports": ["3000:3000"],
                "features": ["Dashboard creation", "Data source plugins", "Alerting"]
            },
            {
                "name": "Jaeger",
                "image": "jaegertracing/all-in-one:latest",
                "kind": "linux",
                "description": "Distributed tracing platform",
                "vendor": "Jaeger Community",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/jaegertracing",
                "ports": ["16686:16686", "14268:14268"],
                "features": ["Distributed tracing", "Service map", "Performance monitoring"]
            },
            {
                "name": "Zipkin",
                "image": "openzipkin/zipkin:latest",
                "kind": "linux",
                "description": "Distributed tracing system",
                "vendor": "OpenZipkin",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/openzipkin",
                "ports": ["9411:9411"],
                "features": ["Trace collection", "Timeline view", "Service dependencies"]
            },
            {
                "name": "Logstash",
                "image": "elasticsearch:8.11.0",
                "kind": "linux",
                "description": "Server-side data processing pipeline",
                "vendor": "Elastic",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.elastic.co/logstash",
                "ports": ["5044:5044", "9600:9600"],
                "features": ["Data transformation", "Multiple inputs", "Filter plugins"]
            },
            {
                "name": "Kibana",
                "image": "kibana:8.11.0",
                "kind": "linux",
                "description": "Data visualization dashboard for Elasticsearch",
                "vendor": "Elastic",
                "category": "monitoring_observability",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.elastic.co/kibana",
                "ports": ["5601:5601"],
                "features": ["Data visualization", "Dashboard creation", "Search interface"]
            }
        ]
        return monitoring_containers
        
    async def discover_analytics_containers(self) -> List[Dict]:
        """Discover analytics and data processing containers"""
        analytics_containers = [
            {
                "name": "Apache Spark",
                "image": "bitnami/spark:latest",
                "kind": "linux",
                "description": "Unified analytics engine for large-scale data processing",
                "vendor": "Apache Software Foundation",
                "category": "analytics",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/bitnami",
                "ports": ["8080:8080", "7077:7077"],
                "features": ["Batch processing", "Stream processing", "ML libraries"]
            },
            {
                "name": "Apache Airflow",
                "image": "apache/airflow:latest",
                "kind": "linux",
                "description": "Platform for workflow automation and scheduling",
                "vendor": "Apache Software Foundation",
                "category": "analytics",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/apache",
                "ports": ["8080:8080"],
                "features": ["Workflow automation", "DAG scheduling", "Web interface"]
            },
            {
                "name": "Superset",
                "image": "apache/superset:latest",
                "kind": "linux",
                "description": "Business intelligence web application",
                "vendor": "Apache Software Foundation",
                "category": "analytics",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/apache",
                "ports": ["8088:8088"],
                "features": ["Data exploration", "Dashboard creation", "SQL Lab"]
            },
            {
                "name": "Metabase",
                "image": "metabase/metabase:latest",
                "kind": "linux",
                "description": "Business intelligence tool for data visualization",
                "vendor": "Metabase",
                "category": "analytics",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/metabase",
                "ports": ["3000:3000"],
                "features": ["Query builder", "Dashboard sharing", "Alert notifications"]
            }
        ]
        return analytics_containers
        
    async def discover_testing_containers(self) -> List[Dict]:
        """Discover testing and load generation containers"""
        testing_containers = [
            {
                "name": "JMeter",
                "image": "justb4/jmeter:latest",
                "kind": "linux",
                "description": "Load testing tool for web applications",
                "vendor": "Apache Software Foundation",
                "category": "testing_load",
                "architecture": ["amd64"],
                "access": "public",
                "registry": "docker.io/justb4",
                "features": ["Load testing", "Performance testing", "GUI and CLI"]
            },
            {
                "name": "k6",
                "image": "grafana/k6:latest",
                "kind": "linux",
                "description": "Modern load testing tool for developers",
                "vendor": "Grafana Labs",
                "category": "testing_load",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/grafana",
                "features": ["JavaScript scripting", "Cloud integration", "Developer-centric"]
            },
            {
                "name": "Locust",
                "image": "locustio/locust:latest",
                "kind": "linux",
                "description": "Scalable load testing framework",
                "vendor": "Locust.io",
                "category": "testing_load",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/locustio",
                "ports": ["8089:8089"],
                "features": ["Web UI", "Distributed testing", "Python scripting"]
            },
            {
                "name": "Artillery",
                "image": "artilleryio/artillery:latest",
                "kind": "linux",
                "description": "Cloud-scale load testing toolkit",
                "vendor": "Artillery.io",
                "category": "testing_load",
                "architecture": ["amd64", "arm64"],
                "access": "public",
                "registry": "docker.io/artilleryio",
                "features": ["Real-time metrics", "WebSocket support", "Cloud deployment"]
            }
        ]
        return testing_containers
    
    async def discover_vrnetlab_built_containers(self) -> List[Dict]:
        """Discover locally built vrnetlab containers"""
        vrnetlab_containers = []
        
        try:
            # Read vrnetlab registry from VRNetlab service data
            vrnetlab_registry_file = self.data_dir / "vrnetlab_containers.json"
            
            if vrnetlab_registry_file.exists():
                with open(vrnetlab_registry_file, 'r') as f:
                    registry = json.load(f)
                
                # Convert registry entries to container list format
                for container_key, container_info in registry.items():
                    vrnetlab_containers.append({
                        "name": container_info["name"],
                        "image": container_info["image"],
                        "description": container_info["description"],
                        "vendor": container_info.get("vendor", "Unknown"),
                        "platform": container_info.get("platform", "Unknown"),
                        "kind": container_info.get("kind", container_info.get("vrnetlab_name", "unknown")),
                        "category": "vrnetlab_built",
                        "access": "local_build",
                        "registry": "local",
                        "build_id": container_info.get("build_id"),
                        "created_at": container_info.get("created_at"),
                        "image_id": container_info.get("image_id"),
                        "features": ["VM-to-Container Conversion", "Local Build", "Ready for Labs"]
                    })
                
                logger.info(f"Found {len(vrnetlab_containers)} vrnetlab built containers")
            else:
                logger.debug("No vrnetlab built containers found")
                
        except Exception as e:
            logger.error(f"Error discovering vrnetlab built containers: {e}")
        
        return vrnetlab_containers
    
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
        
    def search_containers(self, query: str = "", category: str = "", vendor: str = "", architecture: str = "") -> Dict:
        """Search containers with filters"""
        containers = self.load_containers()
        if not containers:
            return {"total": 0, "results": [], "categories": []}
            
        # Collect all matching containers
        results = []
        categories = set()
        
        for category_name, container_list in containers.items():
            if category_name == "last_updated":
                continue
                
            if not isinstance(container_list, list):
                continue
                
            categories.add(category_name)
            
            for container in container_list:
                # Apply filters
                if category and category_name != category:
                    continue
                    
                if vendor and container.get("vendor", "").lower() != vendor.lower():
                    continue
                    
                if architecture:
                    container_archs = container.get("architecture", [])
                    if isinstance(container_archs, list) and architecture not in container_archs:
                        continue
                    elif isinstance(container_archs, str) and container_archs != architecture:
                        continue
                        
                # Apply text search
                if query:
                    query_lower = query.lower()
                    searchable_text = " ".join([
                        container.get("name", ""),
                        container.get("description", ""),
                        container.get("vendor", ""),
                        " ".join(container.get("features", [])),
                        " ".join(container.get("protocols", [])),
                        " ".join(container.get("tools", []))
                    ]).lower()
                    
                    if query_lower not in searchable_text:
                        continue
                
                # Add category information to result
                container_result = container.copy()
                container_result["category_name"] = category_name
                results.append(container_result)
        
        return {
            "total": len(results),
            "results": results,
            "categories": list(categories),
            "query": query,
            "filters": {
                "category": category,
                "vendor": vendor,
                "architecture": architecture
            }
        }
        
    def get_container_categories(self) -> Dict[str, Dict]:
        """Get all container categories with metadata"""
        category_info = {
            "portnox": {
                "name": "Portnox Solutions",
                "description": "Network access control and security solutions",
                "icon": "🔐",
                "color": "#2E7D32"
            },
            "network_os_native": {
                "name": "Native Network OS",
                "description": "Container-native network operating systems",
                "icon": "🖧",
                "color": "#1976D2"
            },
            "network_os_vm_based": {
                "name": "VM-based Network OS",
                "description": "Virtual machine based network operating systems",
                "icon": "💻",
                "color": "#7B1FA2"
            },
            "open_source_network": {
                "name": "Open Source Networking",
                "description": "Open source network operating systems and tools",
                "icon": "🌐",
                "color": "#388E3C"
            },
            "security_firewalls": {
                "name": "Security Firewalls",
                "description": "Enterprise firewall and security appliances",
                "icon": "🛡️",
                "color": "#D32F2F"
            },
            "security": {
                "name": "Security Tools",
                "description": "General security and analysis tools",
                "icon": "🔍",
                "color": "#F57C00"
            },
            "security_pentesting": {
                "name": "Penetration Testing",
                "description": "Offensive security and penetration testing tools",
                "icon": "⚔️",
                "color": "#C62828"
            },
            "security_monitoring": {
                "name": "Security Monitoring",
                "description": "SIEM, IDS/IPS and security monitoring solutions",
                "icon": "👁️",
                "color": "#AD1457"
            },
            "services": {
                "name": "Network Services",
                "description": "Essential network services (DNS, DHCP, RADIUS)",
                "icon": "⚙️",
                "color": "#5D4037"
            },
            "network_simulation": {
                "name": "Network Simulation",
                "description": "Network emulation and simulation platforms",
                "icon": "🎯",
                "color": "#0288D1"
            },
            "network_monitoring": {
                "name": "Network Monitoring",
                "description": "Network monitoring and analysis tools",
                "icon": "📊",
                "color": "#00796B"
            },
            "network_automation": {
                "name": "Network Automation",
                "description": "Network automation and orchestration tools",
                "icon": "🤖",
                "color": "#455A64"
            },
            "development": {
                "name": "Development Tools",
                "description": "IDEs, code editors and development environments",
                "icon": "💻",
                "color": "#6A1B9A"
            },
            "ci_cd": {
                "name": "CI/CD",
                "description": "Continuous integration and deployment tools",
                "icon": "🔄",
                "color": "#2E7D32"
            },
            "databases": {
                "name": "Databases",
                "description": "Relational and NoSQL database systems",
                "icon": "🗄️",
                "color": "#F57C00"
            },
            "message_queues": {
                "name": "Message Queues",
                "description": "Message brokers and streaming platforms",
                "icon": "📮",
                "color": "#689F38"
            },
            "web_servers": {
                "name": "Web Servers",
                "description": "Web servers, proxies and load balancers",
                "icon": "🌍",
                "color": "#0277BD"
            },
            "monitoring_observability": {
                "name": "Monitoring & Observability",
                "description": "Application monitoring and observability tools",
                "icon": "📈",
                "color": "#E64A19"
            },
            "analytics": {
                "name": "Analytics",
                "description": "Data processing and business intelligence tools",
                "icon": "📊",
                "color": "#303F9F"
            },
            "testing_load": {
                "name": "Testing & Load Generation",
                "description": "Load testing and performance testing tools",
                "icon": "⚡",
                "color": "#7B1FA2"
            },
            "vrnetlab_built": {
                "name": "VRNetlab Built",
                "description": "Custom-built containers from VM images",
                "icon": "🏗️",
                "color": "#BF360C"
            }
        }
        
        containers = self.load_containers()
        result = {}
        
        for category_id, info in category_info.items():
            container_count = len(containers.get(category_id, [])) if isinstance(containers.get(category_id, []), list) else 0
            result[category_id] = {
                **info,
                "id": category_id,
                "container_count": container_count
            }
            
        return result
        
    def get_vendors(self) -> List[str]:
        """Get list of all vendors"""
        containers = self.load_containers()
        vendors = set()
        
        for category_name, container_list in containers.items():
            if category_name == "last_updated" or not isinstance(container_list, list):
                continue
                
            for container in container_list:
                vendor = container.get("vendor")
                if vendor:
                    vendors.add(vendor)
                    
        return sorted(list(vendors))
        
    def get_architectures(self) -> List[str]:
        """Get list of all supported architectures"""
        containers = self.load_containers()
        architectures = set()
        
        for category_name, container_list in containers.items():
            if category_name == "last_updated" or not isinstance(container_list, list):
                continue
                
            for container in container_list:
                archs = container.get("architecture", [])
                if isinstance(archs, list):
                    architectures.update(archs)
                elif isinstance(archs, str):
                    architectures.add(archs)
                    
        return sorted(list(architectures))
        
    async def validate_container_compatibility(self, container: Dict, lab_type: str, protocols: List[str] = None) -> Dict:
        """Validate if a container is compatible with a specific lab type"""
        compatibility_score = 0
        recommendations = []
        warnings = []
        
        # Lab type compatibility matrix
        lab_compatibility = {
            "network_simulation": ["network_os_native", "network_os_community", "network_monitoring", "network_automation"],
            "security_testing": ["security_pentesting", "security_monitoring", "security_siem", "network_monitoring"],
            "development": ["development_ide", "development_build", "development_cicd", "infrastructure_database"],
            "monitoring": ["monitoring_metrics", "monitoring_logs", "monitoring_apm", "network_monitoring"],
            "automation": ["network_automation", "development_cicd", "infrastructure_orchestration"]
        }
        
        container_category = container.get("category_name", "")
        compatible_categories = lab_compatibility.get(lab_type, [])
        
        # Check category compatibility
        if container_category in compatible_categories:
            compatibility_score += 50
            recommendations.append(f"Container category '{container_category}' is well-suited for {lab_type} labs")
        elif any(cat in container_category for cat in compatible_categories):
            compatibility_score += 30
            recommendations.append(f"Container category partially matches {lab_type} requirements")
        else:
            warnings.append(f"Container category '{container_category}' may not be optimal for {lab_type} labs")
        
        # Check protocol compatibility if provided
        if protocols:
            container_protocols = container.get("protocols", [])
            if container_protocols:
                matching_protocols = set(protocols) & set(container_protocols)
                if matching_protocols:
                    compatibility_score += 30
                    recommendations.append(f"Supports required protocols: {', '.join(matching_protocols)}")
                else:
                    warnings.append("No matching protocols found")
        
        # Check architecture requirements
        container_archs = container.get("architecture", [])
        if isinstance(container_archs, list) and "amd64" in container_archs:
            compatibility_score += 10
        elif isinstance(container_archs, str) and container_archs == "amd64":
            compatibility_score += 10
        
        # Check access requirements
        access_type = container.get("access", "unknown")
        if access_type == "public":
            compatibility_score += 10
            recommendations.append("Container is publicly available")
        elif access_type in ["registration_required", "cco_required"]:
            warnings.append(f"Container requires {access_type.replace('_', ' ')}")
        
        # Determine compatibility level
        if compatibility_score >= 80:
            compatibility_level = "high"
        elif compatibility_score >= 60:
            compatibility_level = "medium"
        elif compatibility_score >= 40:
            compatibility_level = "low"
        else:
            compatibility_level = "incompatible"
        
        return {
            "compatible": compatibility_score >= 40,
            "compatibility_level": compatibility_level,
            "compatibility_score": compatibility_score,
            "recommendations": recommendations,
            "warnings": warnings
        }
        
    async def get_recommended_containers_for_lab(self, lab_type: str, lab_description: str = None, protocols: List[str] = None, limit: int = 10) -> Dict:
        """Get recommended containers for a specific lab type"""
        all_containers = await self.discover_all_containers()
        recommendations = []
        
        for container in all_containers:
            compatibility = await self.validate_container_compatibility(container, lab_type, protocols)
            
            if compatibility["compatible"]:
                container_with_compat = container.copy()
                container_with_compat["compatibility"] = compatibility
                recommendations.append(container_with_compat)
        
        # Sort by compatibility score (descending)
        recommendations.sort(key=lambda x: x["compatibility"]["compatibility_score"], reverse=True)
        
        return {
            "lab_type": lab_type,
            "recommendations": recommendations[:limit],
            "total_compatible": len([r for r in recommendations if r["compatibility"]["compatibility_level"] in ["high", "medium"]]),
            "total_found": len(recommendations)
        }
        
    async def analyze_lab_container_requirements(self, lab_config: Dict) -> Dict:
        """Analyze a lab configuration and suggest required containers"""
        suggestions = {
            "required_containers": [],
            "optional_containers": [],
            "missing_categories": [],
            "analysis": []
        }
        
        # Extract information from lab config
        lab_nodes = lab_config.get("topology", {}).get("nodes", {})
        lab_kinds = set()
        node_count = len(lab_nodes)
        
        for node_name, node_config in lab_nodes.items():
            node_kind = node_config.get("kind", "unknown")
            lab_kinds.add(node_kind)
        
        # Determine lab type based on node kinds
        if any(kind in ["ceos", "srl", "vr-sros", "vr-xrv9k", "vr-vmx"] for kind in lab_kinds):
            lab_type = "network_simulation"
            suggestions["analysis"].append("Detected network simulation lab with vendor network OS containers")
        elif "linux" in lab_kinds and node_count > 5:
            lab_type = "security_testing"
            suggestions["analysis"].append("Detected multi-node Linux environment suitable for security testing")
        elif "linux" in lab_kinds:
            lab_type = "development"
            suggestions["analysis"].append("Detected Linux-based development environment")
        else:
            lab_type = "general"
            suggestions["analysis"].append("General purpose lab detected")
        
        # Get recommendations based on detected lab type
        recommendations = await self.get_recommended_containers_for_lab(lab_type, limit=20)
        
        # Categorize recommendations
        for container in recommendations["recommendations"]:
            compat_level = container["compatibility"]["compatibility_level"]
            if compat_level == "high":
                suggestions["required_containers"].append(container)
            elif compat_level in ["medium", "low"]:
                suggestions["optional_containers"].append(container)
        
        # Check for missing essential categories
        essential_categories = {
            "network_simulation": ["network_monitoring", "network_automation"],
            "security_testing": ["security_monitoring", "network_monitoring"],
            "development": ["development_build", "infrastructure_database"],
            "general": ["monitoring_metrics"]
        }
        
        required_categories = essential_categories.get(lab_type, [])
        present_categories = set(c["category_name"] for c in suggestions["required_containers"] + suggestions["optional_containers"])
        
        for req_cat in required_categories:
            if req_cat not in present_categories:
                suggestions["missing_categories"].append(req_cat)
        
        suggestions["lab_type"] = lab_type
        suggestions["node_count"] = node_count
        suggestions["detected_kinds"] = list(lab_kinds)
        
        return suggestions
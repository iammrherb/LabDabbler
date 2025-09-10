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
            "network_os": await self.discover_network_os_containers(),
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
    
    async def discover_network_os_containers(self) -> List[Dict]:
        """Discover network operating system containers"""
        network_containers = [
            {
                "name": "nokia-srlinux",
                "image": "ghcr.io/nokia/srlinux:latest",
                "kind": "nokia_srlinux",
                "description": "Nokia SR Linux Network OS",
                "vendor": "nokia",
                "category": "network_os"
            },
            {
                "name": "arista-ceos",
                "image": "ceos:latest",
                "kind": "arista_ceos", 
                "description": "Arista Container EOS",
                "vendor": "arista",
                "category": "network_os"
            },
            {
                "name": "cisco-xrd",
                "image": "localhost/cisco-xrd:latest",
                "kind": "cisco_xrd",
                "description": "Cisco XRd Router",
                "vendor": "cisco",
                "category": "network_os"
            },
            {
                "name": "frr",
                "image": "frrouting/frr:latest",
                "kind": "linux",
                "description": "FRRouting Protocol Suite",
                "vendor": "frrouting",
                "category": "network_os"
            },
            {
                "name": "vyos",
                "image": "vyos/vyos:1.4-rolling",
                "kind": "vyos",
                "description": "VyOS Router",
                "vendor": "vyos", 
                "category": "network_os"
            }
        ]
        
        return network_containers
    
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
                "name": "freeradius",
                "image": "freeradius/freeradius-server:latest",
                "description": "FreeRADIUS Authentication Server",
                "ports": ["1812:1812/udp", "1813:1813/udp"],
                "category": "services"
            },
            {
                "name": "bind9",
                "image": "internetsystemsconsortium/bind9:latest", 
                "description": "BIND9 DNS Server",
                "ports": ["53:53/tcp", "53:53/udp"],
                "category": "services"
            },
            {
                "name": "dhcp-server",
                "image": "networkboot/dhcpd:latest",
                "description": "ISC DHCP Server",
                "category": "services"
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
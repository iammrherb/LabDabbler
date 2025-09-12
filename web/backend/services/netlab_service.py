"""
Netlab Integration Service for LabDabbler

Provides netlab integration for automated topology generation, 
template-based lab creation, and configuration management.
"""

import os
import subprocess
import asyncio
import yaml
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NetlabService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.netlab_data_dir = data_dir / "netlab"
        self.templates_dir = self.netlab_data_dir / "templates"
        self.generated_dir = self.netlab_data_dir / "generated"
        
        # Create directories
        for dir_path in [self.netlab_data_dir, self.templates_dir, self.generated_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Pre-built templates for common scenarios
        self.built_in_templates = {
            "switch_with_endpoints": {
                "name": "Switch with Endpoints",
                "description": "Basic switch topology with configurable number of endpoints",
                "parameters": ["switch_type", "endpoint_count", "enable_8021x"]
            },
            "portnox_radius": {
                "name": "Portnox RADIUS Lab",
                "description": "Network access control lab with Portnox RADIUS server",
                "parameters": ["switch_type", "endpoint_count", "enable_mab"]
            },
            "multi_vendor_bgp": {
                "name": "Multi-Vendor BGP",
                "description": "BGP topology with different vendor platforms",
                "parameters": ["vendors", "as_numbers", "topology_type"]
            },
            "datacenter_fabric": {
                "name": "Data Center Fabric", 
                "description": "Spine-leaf data center topology",
                "parameters": ["spine_count", "leaf_count", "protocol"]
            }
        }
    
    async def check_netlab_installed(self) -> Dict[str, Any]:
        """Check if netlab is installed and get version"""
        try:
            process = await asyncio.create_subprocess_exec(
                "netlab", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=10
            )
            
            if process.returncode == 0:
                version = stdout.decode().strip()
                return {
                    "installed": True,
                    "version": version,
                    "path": shutil.which("netlab")
                }
            else:
                return {
                    "installed": False,
                    "error": stderr.decode().strip()
                }
                
        except (asyncio.TimeoutError, FileNotFoundError) as e:
            return {
                "installed": False,
                "error": f"Netlab not found: {str(e)}"
            }
    
    async def install_netlab(self) -> Dict[str, Any]:
        """Install netlab via pip"""
        try:
            # Install netlab
            process = await asyncio.create_subprocess_exec(
                "pip", "install", "netlab",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=300
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to install netlab: {stderr.decode()}"
                }
            
            # Install containerlab via netlab
            install_process = await asyncio.create_subprocess_exec(
                "netlab", "install", "containerlab",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            install_stdout, install_stderr = await asyncio.wait_for(
                install_process.communicate(), timeout=300
            )
            
            if install_process.returncode != 0:
                logger.warning(f"Containerlab installation warning: {install_stderr.decode()}")
            
            # Verify installation
            version_check = await self.check_netlab_installed()
            
            return {
                "success": True,
                "message": "Netlab installed successfully",
                "version": version_check.get("version", "unknown"),
                "containerlab_install": install_process.returncode == 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to install netlab: {str(e)}"
            }
    
    async def get_netlab_providers(self) -> Dict[str, Any]:
        """Get available netlab providers"""
        try:
            process = await asyncio.create_subprocess_exec(
                "netlab", "show", "providers",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30
            )
            
            if process.returncode == 0:
                # Parse netlab provider output
                providers = {}
                lines = stdout.decode().strip().split('\n')
                current_provider = None
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line and not line.startswith(' '):
                        current_provider = line.split(':')[0].strip()
                        providers[current_provider] = {
                            "name": current_provider,
                            "supported_nodes": [],
                            "description": ""
                        }
                    elif current_provider and line.startswith('  '):
                        # This is likely a supported node type
                        providers[current_provider]["supported_nodes"].append(line.strip())
                
                return {
                    "success": True,
                    "providers": providers
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode().strip()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get providers: {str(e)}"
            }
    
    def create_netlab_topology_template(
        self, 
        template_type: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a netlab topology template based on type and parameters"""
        
        templates = {
            "switch_with_endpoints": self._create_switch_endpoints_template,
            "portnox_radius": self._create_portnox_radius_template,
            "multi_vendor_bgp": self._create_multi_vendor_bgp_template,
            "datacenter_fabric": self._create_datacenter_fabric_template
        }
        
        if template_type not in templates:
            return {
                "success": False,
                "error": f"Unknown template type: {template_type}"
            }
        
        try:
            topology = templates[template_type](parameters)
            return {
                "success": True,
                "topology": topology,
                "template_type": template_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create template: {str(e)}"
            }
    
    def _create_switch_endpoints_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create switch with endpoints template"""
        switch_type = params.get("switch_type", "eos")
        endpoint_count = params.get("endpoint_count", 2)
        enable_8021x = params.get("enable_8021x", False)
        
        # Map switch types to netlab/containerlab kinds
        switch_mapping = {
            "eos": {"kind": "ceos", "image": "ceos:4.32.0F"},
            "arista": {"kind": "ceos", "image": "ceos:4.32.0F"},
            "vyos": {"kind": "vyos", "image": "vyos/vyos:1.4"},
            "frr": {"kind": "linux", "image": "frr:8.0"},
        }
        
        switch_config = switch_mapping.get(switch_type, switch_mapping["eos"])
        
        topology = {
            "defaults": {
                "device": switch_type
            },
            "provider": "clab",
            "nodes": {
                "switch": {
                    **switch_config,
                    "mgmt": {"ipv4": "192.168.121.10/24"}
                }
            },
            "links": []
        }
        
        # Add endpoints
        for i in range(1, endpoint_count + 1):
            endpoint_name = f"endpoint{i}"
            topology["nodes"][endpoint_name] = {
                "kind": "linux",
                "image": "alpine:latest",
                "mgmt": {"ipv4": f"192.168.121.{10 + i}/24"}
            }
            
            # Create links
            topology["links"].append({
                "switch": f"eth{i}",
                endpoint_name: "eth1"
            })
        
        # Add 802.1X configuration if enabled
        if enable_8021x:
            topology["defaults"]["features"] = ["radius"]
            topology["nodes"]["switch"]["config"] = {
                "aaa": {
                    "authentication": {
                        "dot1x": "default group radius"
                    }
                }
            }
        
        return topology
    
    def _create_portnox_radius_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Portnox RADIUS lab template"""
        switch_type = params.get("switch_type", "eos")
        endpoint_count = params.get("endpoint_count", 2)
        enable_mab = params.get("enable_mab", True)
        
        # Base switch topology
        base_topology = self._create_switch_endpoints_template({
            "switch_type": switch_type,
            "endpoint_count": endpoint_count,
            "enable_8021x": True
        })
        
        # Add Portnox RADIUS server
        base_topology["nodes"]["portnox-radius"] = {
            "kind": "linux",
            "image": "portnox/portnox-radius:latest",
            "mgmt": {"ipv4": "192.168.121.100/24"},
            "env": {
                "PORTNOX_LICENSE_KEY": "${PORTNOX_LICENSE_KEY}",
                "RADIUS_SECRET": "testing123"
            },
            "ports": ["1812:1812/udp", "1813:1813/udp", "8080:8080"]
        }
        
        # Add ZTNA Gateway if requested
        if params.get("enable_ztna", False):
            base_topology["nodes"]["ztna-gateway"] = {
                "kind": "linux", 
                "image": "portnox/ztna-gateway:latest",
                "mgmt": {"ipv4": "192.168.121.101/24"},
                "env": {
                    "ZTNA_LICENSE_KEY": "${ZTNA_LICENSE_KEY}",
                    "RADIUS_SERVER": "192.168.121.100"
                }
            }
        
        # Update switch configuration for RADIUS
        base_topology["nodes"]["switch"]["config"] = {
            "aaa": {
                "authentication": {
                    "dot1x": "default group radius",
                    "mac-auth-bypass": enable_mab
                },
                "radius": {
                    "server": {
                        "192.168.121.100": {
                            "key": "testing123",
                            "auth-port": 1812,
                            "acct-port": 1813
                        }
                    }
                }
            }
        }
        
        return base_topology
    
    def _create_multi_vendor_bgp_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create multi-vendor BGP template"""
        vendors = params.get("vendors", ["eos", "vyos"])
        as_numbers = params.get("as_numbers", [65001, 65002])
        topology_type = params.get("topology_type", "full_mesh")
        
        topology = {
            "defaults": {
                "device": "eos"
            },
            "provider": "clab",
            "addressing": {
                "loopback": {"ipv4": "10.0.0.0/24"},
                "p2p": {"ipv4": "10.1.0.0/16"}
            },
            "bgp": {
                "as": 65000
            },
            "nodes": {},
            "links": []
        }
        
        # Create nodes for each vendor
        for i, vendor in enumerate(vendors):
            node_name = f"{vendor}-router{i+1}"
            as_number = as_numbers[i] if i < len(as_numbers) else 65000 + i
            
            device_mapping = {
                "eos": {"kind": "ceos", "image": "ceos:4.32.0F"},
                "vyos": {"kind": "vyos", "image": "vyos/vyos:1.4"},
                "frr": {"kind": "linux", "image": "frr:8.0"}
            }
            
            node_config = device_mapping.get(vendor, device_mapping["eos"])
            topology["nodes"][node_name] = {
                **node_config,
                "bgp": {"as": as_number}
            }
        
        # Create links based on topology type
        nodes = list(topology["nodes"].keys())
        if topology_type == "full_mesh":
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    topology["links"].append([node1, node2])
        elif topology_type == "linear":
            for i in range(len(nodes) - 1):
                topology["links"].append([nodes[i], nodes[i+1]])
        
        return topology
    
    def _create_datacenter_fabric_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create data center fabric template"""
        spine_count = params.get("spine_count", 2)
        leaf_count = params.get("leaf_count", 4)
        protocol = params.get("protocol", "ebgp")
        
        topology = {
            "defaults": {
                "device": "eos"
            },
            "provider": "clab",
            "addressing": {
                "loopback": {"ipv4": "10.0.0.0/24"},
                "p2p": {"ipv4": "10.1.0.0/16"}
            },
            "nodes": {},
            "links": []
        }
        
        # Add protocol-specific configuration
        if protocol == "ebgp":
            topology["bgp"] = {"as": 65000}
        elif protocol == "ospf":
            topology["ospf"] = {"area": "0.0.0.0"}
        
        # Create spine nodes
        for i in range(1, spine_count + 1):
            spine_name = f"spine{i}"
            topology["nodes"][spine_name] = {
                "kind": "ceos",
                "image": "ceos:4.32.0F",
                "role": "spine"
            }
            
            if protocol == "ebgp":
                topology["nodes"][spine_name]["bgp"] = {"as": 65000 + i}
        
        # Create leaf nodes  
        for i in range(1, leaf_count + 1):
            leaf_name = f"leaf{i}"
            topology["nodes"][leaf_name] = {
                "kind": "ceos", 
                "image": "ceos:4.32.0F",
                "role": "leaf"
            }
            
            if protocol == "ebgp":
                topology["nodes"][leaf_name]["bgp"] = {"as": 65100 + i}
        
        # Create spine-leaf links (full mesh)
        for spine_num in range(1, spine_count + 1):
            for leaf_num in range(1, leaf_count + 1):
                topology["links"].append([f"spine{spine_num}", f"leaf{leaf_num}"])
        
        return topology
    
    async def generate_lab_from_template(
        self, 
        template_type: str, 
        parameters: Dict[str, Any],
        lab_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete lab from a template"""
        try:
            # Generate topology
            template_result = self.create_netlab_topology_template(template_type, parameters)
            
            if not template_result["success"]:
                return template_result
            
            topology = template_result["topology"]
            lab_name = lab_name or f"{template_type}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Save netlab topology file
            netlab_file = self.generated_dir / f"{lab_name}.yml"
            with open(netlab_file, 'w') as f:
                yaml.dump(topology, f, default_flow_style=False, indent=2)
            
            # Generate containerlab file using netlab
            clab_result = await self._netlab_create_containerlab(str(netlab_file), lab_name)
            
            if not clab_result["success"]:
                return clab_result
            
            return {
                "success": True,
                "lab_name": lab_name,
                "netlab_file": str(netlab_file),
                "containerlab_file": clab_result["containerlab_file"],
                "topology": topology,
                "generated_files": clab_result.get("generated_files", []),
                "message": f"Lab '{lab_name}' generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate lab from template: {e}")
            return {
                "success": False,
                "error": f"Failed to generate lab: {str(e)}"
            }
    
    async def _netlab_create_containerlab(self, netlab_file: str, lab_name: str) -> Dict[str, Any]:
        """Use netlab to create containerlab topology"""
        try:
            # Change to the directory containing the netlab file
            netlab_path = Path(netlab_file)
            work_dir = netlab_path.parent
            
            # Run netlab create
            process = await asyncio.create_subprocess_exec(
                "netlab", "create", netlab_path.name, "--provider", "clab",
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=120
            )
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Netlab create failed: {stderr.decode()}"
                }
            
            # Look for generated containerlab file
            clab_file = work_dir / f"{netlab_path.stem}.clab.yml"
            if not clab_file.exists():
                # Try alternative naming
                clab_file = work_dir / "clab.yml"
            
            if not clab_file.exists():
                return {
                    "success": False,
                    "error": "Generated containerlab file not found"
                }
            
            # Find any additional generated files
            generated_files = []
            for file_path in work_dir.glob("*"):
                if file_path.is_file() and file_path != netlab_path:
                    generated_files.append(str(file_path))
            
            return {
                "success": True,
                "containerlab_file": str(clab_file),
                "generated_files": generated_files,
                "output": stdout.decode()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create containerlab topology: {str(e)}"
            }
    
    async def list_generated_labs(self) -> Dict[str, Any]:
        """List all generated labs"""
        try:
            labs = []
            
            for netlab_file in self.generated_dir.glob("*.yml"):
                try:
                    with open(netlab_file, 'r') as f:
                        topology = yaml.safe_load(f)
                    
                    # Look for corresponding containerlab file
                    clab_file = netlab_file.with_suffix('.clab.yml')
                    
                    lab_info = {
                        "name": netlab_file.stem,
                        "netlab_file": str(netlab_file),
                        "containerlab_file": str(clab_file) if clab_file.exists() else None,
                        "created": datetime.fromtimestamp(netlab_file.stat().st_mtime).isoformat(),
                        "nodes": len(topology.get("nodes", {})),
                        "links": len(topology.get("links", [])),
                        "provider": topology.get("provider", "unknown")
                    }
                    
                    labs.append(lab_info)
                    
                except Exception as e:
                    logger.error(f"Error reading lab file {netlab_file}: {e}")
                    continue
            
            # Sort by creation time (newest first)
            labs.sort(key=lambda x: x["created"], reverse=True)
            
            return {
                "success": True,
                "labs": labs,
                "total": len(labs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list labs: {str(e)}"
            }
    
    def get_built_in_templates(self) -> Dict[str, Any]:
        """Get list of built-in templates"""
        return {
            "success": True,
            "templates": self.built_in_templates
        }
    
    async def validate_netlab_topology(self, topology_file: str) -> Dict[str, Any]:
        """Validate a netlab topology file"""
        try:
            process = await asyncio.create_subprocess_exec(
                "netlab", "validate", topology_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30
            )
            
            return {
                "success": process.returncode == 0,
                "valid": process.returncode == 0,
                "output": stdout.decode(),
                "errors": stderr.decode() if process.returncode != 0 else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to validate topology: {str(e)}"
            }
"""
Containerlab Configuration Templates Service

This service provides YAML configuration templates for all supported containerlab kinds.
Each template includes proper configuration options, environment variables, and deployment notes.
"""

import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ContainerlabTemplateService:
    """Service to generate containerlab configuration templates for different kinds"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict]:
        """Initialize all containerlab kind templates using ONLY canonical names from containerlab nodes directory"""
        return {
            # CANONICAL CONTAINERLAB KINDS - Derived from data/repositories/containerlab-official/nodes/
            # These are the exact 50 canonical kinds that containerlab recognizes
            
            # Infrastructure and Container kinds
            "6wind_vsr": self._get_6wind_vsr_template(),
            "bridge": self._get_bridge_template(),
            "ext_container": self._get_ext_container_template(),
            "generic_vm": self._get_generic_vm_template(),
            "host": self._get_host_template(),
            "k8s_kind": self._get_k8s_kind_template(),
            "linux": self._get_linux_template(),
            "ovs": self._get_ovs_template(),
            "state": self._get_state_template(),
            
            # Network OS kinds
            "c8000": self._get_cisco_c8000_template(),
            "ceos": self._get_arista_ceos_template(),
            "checkpoint_cloudguard": self._get_checkpoint_cloudguard_template(),
            "cjunosevolved": self._get_juniper_cjunosevolved_template(),
            "crpd": self._get_juniper_crpd_template(),
            "cvx": self._get_cumulus_cvx_template(),
            "dell_sonic": self._get_dell_sonic_template(),
            "fdio_vpp": self._get_fdio_vpp_template(),
            "fortinet_fortigate": self._get_fortinet_fortigate_template(),
            "huawei_vrp": self._get_huawei_vrp_template(),
            "iol": self._get_cisco_iol_template(),
            "ipinfusion_ocnos": self._get_ipinfusion_ocnos_template(),
            "keysight_ixiacone": self._get_keysight_ixiacone_template(),
            "rare": self._get_rare_template(),
            "sonic": self._get_sonic_template(),
            "sonic_vm": self._get_sonic_vm_template(),
            "srl": self._get_nokia_srlinux_template(),
            "sros": self._get_nokia_sros_template(),
            "vyosnetworks_vyos": self._get_vyosnetworks_vyos_template(),
            "xrd": self._get_cisco_xrd_template(),
            
            # Virtual Router (VR) kinds - vrnetlab based
            "vr_aoscx": self._get_aruba_aoscx_template(),
            "vr_c8000v": self._get_cisco_c8000v_template(),
            "vr_cat9kv": self._get_cisco_cat9kv_template(),
            "vr_csr": self._get_cisco_csr1000v_template(),
            "vr_freebsd": self._get_freebsd_template(),
            "vr_ftdv": self._get_cisco_ftdv_template(),
            "vr_ftosv": self._get_dell_ftos_template(),
            "vr_n9kv": self._get_cisco_n9kv_template(),
            "vr_openbsd": self._get_openbsd_template(),
            "vr_openwrt": self._get_openwrt_template(),
            "vr_pan": self._get_paloalto_panos_template(),
            "vr_ros": self._get_mikrotik_ros_template(),
            "vr_sros": self._get_nokia_vr_sros_template(),
            "vr_veos": self._get_arista_veos_template(),
            "vr_vjunosevolved": self._get_juniper_vjunosevolved_template(),
            "vr_vjunosswitch": self._get_juniper_vjunosswitch_template(),
            "vr_vmx": self._get_juniper_vmx_template(),
            "vr_vqfx": self._get_juniper_vqfx_template(),
            "vr_vsrx": self._get_juniper_vsrx_template(),
            "vr_xrv": self._get_cisco_xrv_template(),
            "vr_xrv9k": self._get_cisco_xrv9k_template()
        }
    
    def generate_topology(self, 
                         lab_name: str,
                         nodes: List[Dict],
                         links: Optional[List[Dict]] = None,
                         mgmt_config: Optional[Dict] = None) -> str:
        """Generate complete containerlab topology YAML"""
        
        topology = {
            "name": lab_name,
            "topology": {
                "kinds": {},
                "nodes": {},
                "links": links or []
            }
        }
        
        # Add management configuration if provided
        if mgmt_config:
            topology["mgmt"] = mgmt_config
        
        # Process nodes and collect kinds
        kinds_used = set()
        for node in nodes:
            node_id = node["id"]
            node_kind = node["kind"]
            
            # Get template for this kind
            template = self.templates.get(node_kind, {})
            
            # Build node configuration
            node_config = {
                "kind": node_kind,
                "image": node.get("image", template.get("default_image", "")),
            }
            
            # Add kind-specific configuration
            if "default_type" in template:
                node_config["type"] = node.get("type", template["default_type"])
            
            if "env" in template:
                node_config["env"] = {**template["env"], **node.get("env", {})}
            
            if "sysctls" in template:
                node_config["sysctls"] = template["sysctls"]
            
            if "capabilities" in template:
                node_config["cap_add"] = template["capabilities"]
            
            if "ports" in node and node["ports"]:
                node_config["ports"] = node["ports"]
            
            if "volumes" in node and node["volumes"]:
                node_config["binds"] = node["volumes"]
            
            if "startup_config" in node and node["startup_config"]:
                node_config["startup-config"] = node["startup_config"]
            
            if "license" in node and node["license"]:
                node_config["license"] = node["license"]
            
            topology["topology"]["nodes"][node_id] = node_config
            kinds_used.add(node_kind)
        
        # Add kind-level configurations
        for kind in kinds_used:
            template = self.templates.get(kind, {})
            if "kind_config" in template:
                topology["topology"]["kinds"][kind] = template["kind_config"]
        
        # Convert to YAML
        return yaml.dump(topology, default_flow_style=False, sort_keys=False, indent=2)
    
    def get_kind_template(self, kind: str) -> Dict:
        """Get template for a specific kind"""
        return self.templates.get(kind, {})
    
    def get_supported_kinds(self) -> List[str]:
        """Get list of all supported canonical containerlab kinds"""
        return sorted(list(self.templates.keys()))
    
    def get_canonical_kinds_from_source(self) -> List[str]:
        """Get canonical kinds directly from containerlab-official nodes directory"""
        nodes_dir = Path("data/repositories/containerlab-official/nodes")
        if not nodes_dir.exists():
            logger.warning(f"Containerlab nodes directory not found: {nodes_dir}")
            return []
        
        canonical_kinds = []
        for item in nodes_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                canonical_kinds.append(item.name)
        
        return sorted(canonical_kinds)
    
    def validate_templates_against_canonical(self) -> Dict[str, Any]:
        """Validate that all template keys match canonical containerlab kinds"""
        canonical_kinds = set(self.get_canonical_kinds_from_source())
        template_kinds = set(self.templates.keys())
        
        missing_from_templates = canonical_kinds - template_kinds
        extra_in_templates = template_kinds - canonical_kinds
        matching_kinds = canonical_kinds & template_kinds
        
        return {
            "canonical_count": len(canonical_kinds),
            "template_count": len(template_kinds),
            "matching_count": len(matching_kinds),
            "missing_from_templates": sorted(list(missing_from_templates)),
            "extra_in_templates": sorted(list(extra_in_templates)),
            "coverage_percentage": round((len(matching_kinds) / len(canonical_kinds)) * 100, 2) if canonical_kinds else 0,
            "validation_passed": len(extra_in_templates) == 0 and len(missing_from_templates) == 0
        }
    
    def validate_node_config(self, kind: str, config: Dict) -> List[str]:
        """Validate node configuration against kind requirements"""
        errors = []
        template = self.templates.get(kind)
        
        if not template:
            errors.append(f"Unsupported kind: {kind}")
            return errors
        
        # Check required fields
        required_fields = template.get("required_fields", [])
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Required field '{field}' is missing")
        
        # Check image format
        if "image_pattern" in template and config.get("image"):
            import re
            pattern = template["image_pattern"]
            if not re.match(pattern, config["image"]):
                errors.append(f"Image '{config['image']}' does not match expected pattern for {kind}")
        
        return errors
    
    # Nokia Templates
    def _get_nokia_srlinux_template(self) -> Dict:
        return {
            "default_image": "ghcr.io/nokia/srlinux:latest",
            "default_type": "ixr-d2l",
            "env": {
                "TINI_SUBREAPER": "1",
                "SRLINUX": "1"
            },
            "sysctls": {
                "net.ipv4.ip_forward": "0",
                "net.ipv6.conf.all.disable_ipv6": "0",
                "net.ipv6.conf.all.accept_dad": "0",
                "net.ipv6.conf.default.accept_dad": "0",
                "net.ipv6.conf.all.autoconf": "0",
                "net.ipv6.conf.default.autoconf": "0"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "kind_config": {
                "image": "ghcr.io/nokia/srlinux:latest"
            },
            "required_fields": ["image"],
            "image_pattern": r".*srlinux.*",
            "ports": ["21022:22", "21830:830", "21831:8080"],
            "documentation": "https://learn.srlinux.dev/",
            "default_credentials": {"username": "admin", "password": "NokiaSrl1!"},
            "notes": [
                "Supports multiple device types via 'type' parameter",
                "Default type is 'ixr-d2l' for datacenter use cases",
                "NETCONF available on port 830, HTTP on 8080",
                "Also registered as 'srl' for short name compatibility"
            ]
        }
    
    def _get_nokia_sros_template(self) -> Dict:
        """Canonical Nokia SROS template - container-based SR-SIM simulation"""
        return {
            "default_image": "nokia/sros:latest",
            "default_type": "SR-1",
            "env": {
                "SRSIM": "1",
                "NOKIA_SROS_CHASSIS": "SR-1",
                "NOKIA_SROS_SYSTEM_BASE_MAC": "fa:ac:ff:ff:10:00",
                "NOKIA_SROS_SLOT": "A"
            },
            "sysctls": {
                "net.ipv4.ip_forward": "0",
                "net.ipv6.conf.all.disable_ipv6": "0",
                "net.ipv6.conf.default.disable_ipv6": "0",
                "net.ipv6.conf.all.accept_dad": "0",
                "net.ipv6.conf.default.accept_dad": "0",
                "net.ipv6.conf.all.autoconf": "0",
                "net.ipv6.conf.default.autoconf": "0",
                "net.ipv4.conf.all.rp_filter": "0",
                "net.ipv6.conf.all.accept_ra": "0",
                "net.ipv6.conf.default.accept_ra": "0",
                "net.ipv4.conf.default.rp_filter": "0"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"],
            "required_fields": ["image"],
            "image_pattern": r".*sros.*",
            "ports": ["22022:22", "22830:830", "21443:443"],
            "documentation": "https://containerlab.dev/manual/kinds/sros/",
            "default_credentials": {"username": "admin", "password": "NokiaSros1!"},
            "notes": [
                "Container-based Nokia SR OS simulation (SR-SIM)",
                "Native containerized implementation",
                "Default chassis type is SR-1, configurable via type parameter",
                "NETCONF available on port 830, HTTPS on 443"
            ]
        }
    
    def _get_nokia_vr_sros_template(self) -> Dict:
        """Nokia VR-SROS template - vrnetlab-based VM version"""
        return {
            "default_image": "vrnetlab/vr-sros:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image", "license"],
            "image_pattern": r".*vr-sros.*",
            "documentation": "https://containerlab.dev/manual/kinds/vr-sros/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "VM-based Nokia SR OS using vrnetlab infrastructure",
                "License file required for operation",
                "Supports all SR OS features and protocols",
                "Requires vrnetlab build from Nokia images"
            ]
        }
    
    def _get_nokia_srsim_template(self) -> Dict:
        return {
            "default_image": "nokia/srsim:latest",
            "env": {"SRSIM_MODE": "1"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/sros/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "Nokia SR OS simulator for testing",
                "Container-based lightweight version",
                "Limited feature set compared to full SR OS"
            ]
        }
    
    # Arista Templates
    def _get_arista_ceos_template(self) -> Dict:
        return {
            "default_image": "ceos:latest",
            "env": {
                "CEOS": "1",
                "EOS_PLATFORM": "ceossim",
                "container": "docker"
            },
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_NICE", "NET_BROADCAST", "SYS_PTRACE"],
            "required_fields": ["image"],
            "image_pattern": r"ceos:.*",
            "ports": ["22443:443", "22022:22"],
            "documentation": "https://containerlab.dev/manual/kinds/ceos/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "Download from arista.com requires account",
                "Native container implementation of EOS",
                "Full EOS feature support in container"
            ]
        }
    
    def _get_arista_veos_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-veos:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-veos/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "VM-based Arista vEOS using vrnetlab",
                "Requires manual build from Arista images",
                "Full EOS feature support"
            ]
        }
    
    # Juniper Templates  
    def _get_juniper_crpd_template(self) -> Dict:
        return {
            "default_image": "crpd:latest",
            "env": {"CRPD": "1"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"],
            "required_fields": ["image"],
            "ports": ["22830:830", "22022:22"],
            "documentation": "https://containerlab.dev/manual/kinds/crpd/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "Containerized Routing Protocol Daemon",
                "Full Junos CLI and routing protocols",
                "Requires Juniper enterprise registry access"
            ]
        }
    
    def _get_juniper_vmx_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vmx:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vmx/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "VM-based Juniper vMX router",
                "Full MX-series feature support",
                "Requires vrnetlab build from Juniper images"
            ]
        }
    
    def _get_juniper_vqfx_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vqfx:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vqfx/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "VM-based Juniper vQFX switch",
                "QFX-series switching features",
                "Requires vrnetlab build"
            ]
        }
    
    def _get_juniper_vsrx_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vsrx:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vsrx/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "VM-based Juniper vSRX firewall",
                "SRX-series security features",
                "Requires vrnetlab build"
            ]
        }
    
    def _get_juniper_vjunosrouter_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vjunosrouter:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vjunosrouter/",
            "default_credentials": {"username": "root", "password": "admin"}
        }
    
    def _get_juniper_vjunosswitch_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vjunosswitch:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vjunosswitch/",
            "default_credentials": {"username": "root", "password": "admin"}
        }
    
    def _get_juniper_vjunosevolved_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-vjunosevolved:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-vjunosevolved/",
            "default_credentials": {"username": "root", "password": "admin"}
        }
    
    # Cisco Templates
    def _get_cisco_xrd_template(self) -> Dict:
        return {
            "default_image": "localhost/ios-xr:latest",
            "env": {"XR_FIRST_BOOT_CONFIG": "/etc/xrd/startup.cfg"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "NET_RAW"],
            "required_fields": ["image"],
            "ports": ["22022:22", "22830:830"],
            "documentation": "https://containerlab.dev/manual/kinds/xrd/",
            "default_credentials": {"username": "clab", "password": "clab@123"},
            "notes": [
                "Native containerized IOS XR",
                "Requires CCO account for download",
                "Full IOS XR feature support"
            ]
        }
    
    def _get_cisco_xrv9k_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-xrv9k:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-xrv9k/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    def _get_cisco_xrv_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-xrv:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-xrv/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    def _get_cisco_csr1000v_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-csr:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-csr/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    def _get_cisco_n9kv_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-n9kv:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-n9kv/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    
    def _get_cisco_cat9kv_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-cat9kv:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-cat9kv/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    def _get_cisco_iol_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/cisco_iol:latest",
            "env": {"IOL": "1"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/cisco_iol/",
            "default_credentials": {"username": "clab", "password": "clab@123"}
        }
    
    def _get_cisco_ftdv_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-ftdv:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-ftdv/",
            "default_credentials": {"username": "admin", "password": "Admin123"}
        }
    
    # Continue with other vendor templates...
    def _get_cumulus_cvx_template(self) -> Dict:
        return {
            "default_image": "cumulus-vx:latest",
            "env": {"CVX": "1"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/cvx/",
            "default_credentials": {"username": "cumulus", "password": "cumulus"}
        }
    
    def _get_aruba_aoscx_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-aoscx:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-aoscx/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    # Add remaining templates for brevity...
    def _get_sonic_template(self) -> Dict:
        return {
            "default_image": "docker-sonic-vs:latest",
            "env": {"SONIC_PLATFORM": "vs"},
            "syscalls": ["sys_admin"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/sonic-vs/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_sonic_vm_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/sonic-vm:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/sonic-vm/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_dell_ftos_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-ftosv:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-ftosv/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_dell_sonic_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/dell_sonic:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/dell_sonic/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_mikrotik_ros_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-ros:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-ros/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_huawei_vrp_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/huawei_vrp:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/huawei_vrp/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_ipinfusion_ocnos_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/ipinfusion-ocnos:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/ipinfusion-ocnos/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    # Security Templates
    def _get_checkpoint_cloudguard_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/checkpoint_cloudguard:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/checkpoint_cloudguard/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_fortinet_fortigate_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/fortinet_fortigate:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/fortinet_fortigate/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_paloalto_panos_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-pan:latest",
            "env": {
                "CONNECTION_MODE": "vrnetlab",
                "USERNAME": "admin",
                "PASSWORD": "Admin@123",
                "VCPU": "2",
                "RAM": "6144"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-pan/",
            "default_credentials": {"username": "admin", "password": "Admin@123"}
        }
    
    # Open Source Templates
    def _get_fdio_vpp_template(self) -> Dict:
        return {
            "default_image": "ligato/vpp-base:latest",
            "env": {"VPP": "1"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/fdio_vpp/",
            "default_credentials": {"username": "root", "password": "vpp"}
        }
    
    def _get_6wind_vsr_template(self) -> Dict:
        return {
            "default_image": "6wind/6wind-vsr:latest",
            "env": {"VSR": "1"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/6wind_vsr/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_rare_template(self) -> Dict:
        return {
            "default_image": "rare/freeRtr:latest",
            "env": {"RARE": "1"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/rare-freertr/",
            "default_credentials": {"username": "rare", "password": "rare"}
        }
    
    def _get_keysight_ixiacone_template(self) -> Dict:
        return {
            "default_image": "ghcr.io/open-traffic-generator/ixia-c-one:latest",
            "env": {"IXIA_C_ONE": "1"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "ports": ["11443:443", "12400:12400"],
            "documentation": "https://containerlab.dev/manual/kinds/keysight_ixia-c-one/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    def _get_openbsd_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/openbsd:latest",
            "env": {
                "CONNECTION_MODE": "vrnetlab",
                "USERNAME": "admin",
                "PASSWORD": "admin",
                "VCPU": "1",
                "RAM": "1024"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/openbsd/",
            "default_credentials": {"username": "admin", "password": "admin"}
        }
    
    # Infrastructure Templates
    def _get_linux_template(self) -> Dict:
        return {
            "default_image": "alpine:latest",
            "env": {"CONTAINER_TYPE": "linux"},
            "capabilities": ["NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/linux/",
            "default_credentials": {"username": "root", "password": "root"}
        }
    
    def _get_bridge_template(self) -> Dict:
        return {
            "default_image": "N/A",
            "capabilities": ["NET_ADMIN"],
            "documentation": "https://containerlab.dev/manual/kinds/bridge/",
            "notes": ["Software bridge - no container required"]
        }
    
    def _get_ovs_template(self) -> Dict:
        return {
            "default_image": "openvswitch/ovs:latest",
            "capabilities": ["NET_ADMIN", "SYS_ADMIN"],
            "documentation": "https://containerlab.dev/manual/kinds/ovs-bridge/",
            "notes": ["OpenVSwitch bridge - software switch"]
        }
    
    def _get_ext_container_template(self) -> Dict:
        return {
            "default_image": "user-defined",
            "documentation": "https://containerlab.dev/manual/kinds/ext-container/",
            "notes": ["Use existing external container"]
        }
    
    def _get_host_template(self) -> Dict:
        return {
            "default_image": "N/A",
            "documentation": "https://containerlab.dev/manual/kinds/host/",
            "notes": ["Connect to host system network"]
        }
    
    def _get_generic_vm_template(self) -> Dict:
        return {
            "default_image": "user-defined",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "documentation": "https://containerlab.dev/manual/kinds/generic_vm/",
            "notes": ["Generic VM using vrnetlab"]
        }
    
    # Additional Templates for Complete Coverage
    def _get_vyosnetworks_vyos_template(self) -> Dict:
        return {
            "default_image": "vyos/vyos:latest",
            "env": {
                "CONTAINER": "1"
            },
            "sysctls": {
                "net.ipv4.ip_forward": "1",
                "net.ipv6.conf.all.forwarding": "1",
                "net.ipv6.conf.all.disable_ipv6": "0"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "NET_RAW"],
            "required_fields": ["image"],
            "image_pattern": r".*vyos.*",
            "documentation": "https://containerlab.dev/manual/kinds/vyosnetworks_vyos/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "VyOS network operating system",
                "Requires privileged mode for full functionality",
                "Uses config.boot for startup configuration"
            ]
        }
    
    def _get_freebsd_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/freebsd:latest",
            "env": {
                "CONNECTION_MODE": "vrnetlab",
                "USERNAME": "admin",
                "PASSWORD": "admin",
                "VCPU": "1",
                "RAM": "1024"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/freebsd/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "FreeBSD VM using vrnetlab",
                "Unix-like operating system",
                "Suitable for network appliances and testing"
            ]
        }
    
    def _get_openwrt_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/openwrt:latest",
            "env": {
                "CONNECTION_MODE": "vrnetlab",
                "USERNAME": "root",
                "PASSWORD": "admin",
                "VCPU": "1",
                "RAM": "512"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr_openwrt/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "OpenWrt Linux distribution for embedded devices",
                "Commonly used for routers and IoT devices",
                "Lightweight and customizable"
            ]
        }
    
    def _get_k8s_kind_template(self) -> Dict:
        return {
            "default_image": "kindest/node:latest",
            "env": {
                "KUBECONFIG": "/etc/kubernetes/admin.conf"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "ports": ["6443:6443"],  # Kubernetes API server
            "documentation": "https://containerlab.dev/manual/kinds/k8s_kind/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "Kubernetes in Docker (KinD) node",
                "Creates Kubernetes clusters using containers",
                "Useful for testing K8s applications"
            ]
        }
    
    # Missing Templates for Complete Canonical Coverage
    def _get_state_template(self) -> Dict:
        return {
            "default_image": "containerlab/state:latest",
            "env": {},
            "capabilities": ["SYS_ADMIN", "NET_ADMIN"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/state/",
            "notes": [
                "State container for topology state management",
                "Used internally by containerlab for state tracking"
            ]
        }
    
    def _get_juniper_cjunosevolved_template(self) -> Dict:
        return {
            "default_image": "juniper/cjunosevolved:latest",
            "env": {
                "CJUNOS": "1",
                "JUNOS_EVOLVED": "1"
            },
            "sysctls": {
                "net.ipv4.ip_forward": "1",
                "net.ipv6.conf.all.forwarding": "1"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/cjunosevolved/",
            "default_credentials": {"username": "root", "password": "admin"},
            "notes": [
                "Containerized Junos Evolved",
                "Native container version of Junos Evolved",
                "Requires Juniper enterprise registry access"
            ]
        }
    
    def _get_cisco_c8000_template(self) -> Dict:
        return {
            "default_image": "cisco/c8000:latest",
            "env": {
                "C8000": "1",
                "CISCO_PLATFORM": "c8000"
            },
            "sysctls": {
                "net.ipv4.ip_forward": "1",
                "net.ipv6.conf.all.forwarding": "1"
            },
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/c8000/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "Cisco Catalyst 8000 Edge platform",
                "Native container implementation",
                "Enterprise routing and SD-WAN features"
            ]
        }
    
    def _get_cisco_c8000v_template(self) -> Dict:
        return {
            "default_image": "vrnetlab/vr-c8000v:latest",
            "env": {"CONNECTION_MODE": "vrnetlab"},
            "syscalls": ["sys_admin", "sys_resource"],
            "capabilities": ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"],
            "required_fields": ["image"],
            "documentation": "https://containerlab.dev/manual/kinds/vr-c8000v/",
            "default_credentials": {"username": "admin", "password": "admin"},
            "notes": [
                "VM-based Cisco Catalyst 8000V using vrnetlab",
                "Full C8000V feature support",
                "Requires vrnetlab build from Cisco images"
            ]
        }
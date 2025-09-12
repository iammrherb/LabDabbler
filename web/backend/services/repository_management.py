import asyncio
import aiohttp
import aiofiles
import json
import yaml
import subprocess
import os
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class RepositoryManagementService:
    """
    Comprehensive repository management service for LabDabbler.
    Handles cloning, syncing, and managing containerlab repositories from various sources.
    """
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # Directory structure for repository management
        self.repositories_dir = self.data_dir / "repositories"
        self.repositories_dir.mkdir(exist_ok=True)
        
        # Metadata files
        self.repositories_config_file = self.data_dir / "repositories_config.json"
        self.repositories_metadata_file = self.data_dir / "repositories_metadata.json"
        self.sync_status_file = self.data_dir / "sync_status.json"
        
        # GitHub token for authenticated requests
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Background scheduler for automated sync
        self.scheduler = None
        self._scheduler_started = False
        
        # Comprehensive repository sources covering major vendors, communities, and educational institutions
        self.default_sources = {
            "core_repositories": [
                {
                    "name": "containerlab-official",
                    "url": "https://github.com/srl-labs/containerlab.git",
                    "branch": "main",
                    "category": "official",
                    "vendor": "nokia",
                    "description": "Official containerlab examples and documentation",
                    "lab_paths": ["lab-examples/"],
                    "auto_sync": True,
                    "sync_frequency": 86400  # 24 hours
                },
                {
                    "name": "hellt-clabs", 
                    "url": "https://github.com/hellt/clabs.git",
                    "branch": "main",
                    "category": "community",
                    "vendor": "multi-vendor",
                    "description": "Community containerlab topologies by hellt - comprehensive multi-vendor labs",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                },
                {
                    "name": "learn-srlinux",
                    "url": "https://github.com/srl-labs/learn-srlinux.git",
                    "branch": "main", 
                    "category": "educational",
                    "vendor": "nokia",
                    "description": "SR Linux learning labs and tutorials",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                },
                {
                    "name": "packetanglers-topos",
                    "url": "https://github.com/PacketAnglers/clab-topos.git", 
                    "branch": "main",
                    "category": "community",
                    "vendor": "arista",
                    "description": "PacketAnglers containerlab topologies - Arista focused",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 86400
                }
            ],
            "vendor_repositories": [
                {
                    "name": "networkop-k8s-multicast",
                    "url": "https://github.com/networkop/k8s-multicast.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "multi-vendor",
                    "description": "Kubernetes multicast networking labs",
                    "lab_paths": ["clab/"],
                    "auto_sync": True,
                    "sync_frequency": 172800  # 48 hours
                },
                {
                    "name": "networkop-meshnet-cni",
                    "url": "https://github.com/networkop/meshnet-cni.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "multi-vendor",
                    "description": "Meshnet CNI examples and topologies",
                    "lab_paths": ["examples/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "arista-network-ci",
                    "url": "https://github.com/networkop/arista-network-ci.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "arista",
                    "description": "Arista network CI/CD pipeline examples",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "srl-telemetry-lab",
                    "url": "https://github.com/srl-labs/srl-telemetry-lab.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "nokia",
                    "description": "SR Linux telemetry and observability labs",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "srl-bgp-lab",
                    "url": "https://github.com/srl-labs/srl-bgp-lab.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "nokia",
                    "description": "SR Linux BGP configuration and troubleshooting labs",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                }
            ],
            "community_repositories": [
                {
                    "name": "cisco-iol-labs",
                    "url": "https://github.com/ttafsir/eve-ng-labs.git",
                    "branch": "main",
                    "category": "community",
                    "vendor": "cisco",
                    "description": "Cisco IOL and containerlab topology examples",
                    "lab_paths": ["containerlab/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "frr-containerlab-examples",
                    "url": "https://github.com/FRRouting/frr-containerlab.git",
                    "branch": "main",
                    "category": "community",
                    "vendor": "frr",
                    "description": "FRRouting protocol labs and examples",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "sonic-containerlab",
                    "url": "https://github.com/sonic-net/sonic-buildimage.git",
                    "branch": "master",
                    "category": "community",
                    "vendor": "sonic",
                    "description": "SONiC network operating system labs",
                    "lab_paths": ["dockers/docker-sonic-vs/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "cumulus-vx-labs",
                    "url": "https://github.com/CumulusNetworks/cldemo-automation-ansible.git",
                    "branch": "master",
                    "category": "community",
                    "vendor": "cumulus",
                    "description": "Cumulus VX network automation labs",
                    "lab_paths": ["./"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "openconfig-labs",
                    "url": "https://github.com/openconfig/containerlab-demos.git",
                    "branch": "main",
                    "category": "community",
                    "vendor": "multi-vendor",
                    "description": "OpenConfig and gNMI demonstration labs",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                }
            ],
            "educational_repositories": [
                {
                    "name": "network-automation-labs",
                    "url": "https://github.com/networktocode/network-automation-labs.git",
                    "branch": "main",
                    "category": "educational",
                    "vendor": "multi-vendor",
                    "description": "Network automation training labs and examples",
                    "lab_paths": ["labs/", "containerlab/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "instruqt-clab-topologies",
                    "url": "https://github.com/ttafsir/instruqt-clab-topologies.git",
                    "branch": "main",
                    "category": "educational", 
                    "vendor": "multi-vendor",
                    "description": "Instruqt-based containerlab topologies",
                    "lab_paths": ["./"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "network-programmability-labs",
                    "url": "https://github.com/jeremycohoe/network-programmability-labs.git",
                    "branch": "main",
                    "category": "educational",
                    "vendor": "cisco",
                    "description": "Network programmability and automation learning labs",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "bgp-evpn-labs",
                    "url": "https://github.com/dneary/bgp-labs.git",
                    "branch": "main",
                    "category": "educational",
                    "vendor": "multi-vendor",
                    "description": "BGP and EVPN learning laboratories",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "python-networking-labs",
                    "url": "https://github.com/ktbyers/netmiko_tools.git",
                    "branch": "main",
                    "category": "educational",
                    "vendor": "multi-vendor",
                    "description": "Python networking automation labs and tools",
                    "lab_paths": ["examples/", "labs/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                }
            ],
            "specialty_repositories": [
                {
                    "name": "security-labs",
                    "url": "https://github.com/containerlab/network-security-labs.git",
                    "branch": "main",
                    "category": "security",
                    "vendor": "multi-vendor",
                    "description": "Network security and penetration testing labs",
                    "lab_paths": ["labs/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "telemetry-observability-labs",
                    "url": "https://github.com/srl-labs/intent-based-analytics.git",
                    "branch": "main",
                    "category": "telemetry",
                    "vendor": "nokia",
                    "description": "Network telemetry and observability stack",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "mpls-sr-labs",
                    "url": "https://github.com/segment-routing/srv6-labs.git",
                    "branch": "main",
                    "category": "advanced",
                    "vendor": "multi-vendor",
                    "description": "MPLS and Segment Routing v6 laboratories",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "datacenter-labs",
                    "url": "https://github.com/networkop/arista-datacenter-labs.git",
                    "branch": "main",
                    "category": "datacenter",
                    "vendor": "arista",
                    "description": "Modern datacenter architecture labs",
                    "lab_paths": ["./"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                }
            ],
            "additional_sources": [
                {
                    "name": "clab-config-demo",
                    "url": "https://github.com/hellt/clab-config-demo.git",
                    "branch": "main",
                    "category": "demo",
                    "vendor": "multi-vendor",
                    "description": "Containerlab configuration demonstration and best practices",
                    "lab_paths": ["./"],
                    "auto_sync": False,
                    "sync_frequency": 604800  # 7 days
                },
                {
                    "name": "network-automation-examples",
                    "url": "https://github.com/napalm-automation/napalm-examples.git",
                    "branch": "main",
                    "category": "automation",
                    "vendor": "multi-vendor",
                    "description": "NAPALM network automation examples with containerlab",
                    "lab_paths": ["examples/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                },
                {
                    "name": "juniper-clab-examples",
                    "url": "https://github.com/Juniper/containerlab-juniper.git",
                    "branch": "main",
                    "category": "vendor",
                    "vendor": "juniper",
                    "description": "Juniper vEX and cRPD containerlab examples",
                    "lab_paths": ["labs/"],
                    "auto_sync": True,
                    "sync_frequency": 172800
                },
                {
                    "name": "topology-converter",
                    "url": "https://github.com/CumulusNetworks/topology_converter.git",
                    "branch": "master",
                    "category": "tools",
                    "vendor": "cumulus",
                    "description": "Network topology converter with containerlab support",
                    "lab_paths": ["examples/"],
                    "auto_sync": False,
                    "sync_frequency": 604800
                }
            ]
        }
        
    async def initialize_repositories(self) -> Dict:
        """Initialize the repository management system"""
        try:
            logger.info("Initializing repository management system...")
            
            # Load or create configuration
            config = await self.load_or_create_config()
            
            # Initialize all repository categories
            results = []
            
            # Core repositories (high priority, always sync first)
            for repo_config in config.get("core_repositories", []):
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
            
            # Vendor repositories (if enabled)
            for repo_config in config.get("vendor_repositories", []):
                if repo_config.get("auto_sync", False):
                    result = await self.clone_or_update_repository(repo_config)
                    results.append(result)
            
            # Community repositories (if enabled)
            for repo_config in config.get("community_repositories", []):
                if repo_config.get("auto_sync", False):
                    result = await self.clone_or_update_repository(repo_config)
                    results.append(result)
            
            # Educational repositories (if enabled)
            for repo_config in config.get("educational_repositories", []):
                if repo_config.get("auto_sync", False):
                    result = await self.clone_or_update_repository(repo_config)
                    results.append(result)
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return {
                "success": True,
                "message": "Repository management system initialized",
                "results": results,
                "total_repositories": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error initializing repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize repository management system"
            }
    
    async def load_or_create_config(self) -> Dict[str, Any]:
        """Load existing configuration or create default configuration"""
        try:
            if self.repositories_config_file.exists():
                async with aiofiles.open(self.repositories_config_file, 'r') as f:
                    content = await f.read()
                    config = json.loads(content)
                logger.info("Loaded existing repository configuration")
            else:
                config: Dict[str, Any] = self.default_sources.copy()
                config["last_updated"] = datetime.now().isoformat()
                config["version"] = "1.0.0"
                
                async with aiofiles.open(self.repositories_config_file, 'w') as f:
                    await f.write(json.dumps(config, indent=2))
                    
                logger.info("Created default repository configuration")
                
            return config
            
        except Exception as e:
            logger.error(f"Error loading/creating config: {e}")
            return self.default_sources.copy()
    
    async def clone_or_update_repository(self, repo_config: Dict) -> Dict:
        """Clone a new repository or update an existing one"""
        repo_name = repo_config["name"]
        repo_url = repo_config["url"]
        branch = repo_config.get("branch", "main")
        repo_path = self.repositories_dir / repo_name
        
        try:
            if repo_path.exists() and (repo_path / ".git").exists():
                # Repository exists, update it
                logger.info(f"Updating repository: {repo_name}")
                
                # Fetch latest changes
                process = await asyncio.create_subprocess_exec(
                    "git", "fetch", "origin", branch,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "update",
                        "error": f"Git fetch failed: {stderr.decode()}"
                    }
                
                # Reset to latest origin
                process = await asyncio.create_subprocess_exec(
                    "git", "reset", "--hard", f"origin/{branch}",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "update", 
                        "error": f"Git reset failed: {stderr.decode()}"
                    }
                    
                action = "updated"
                
            else:
                # Clone new repository
                logger.info(f"Cloning repository: {repo_name}")
                
                # Remove directory if it exists but is not a git repo
                if repo_path.exists():
                    shutil.rmtree(repo_path)
                
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", "-b", branch, repo_url, str(repo_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "repository": repo_name,
                        "action": "clone",
                        "error": f"Git clone failed: {stderr.decode()}"
                    }
                    
                action = "cloned"
            
            # Scan for labs in this repository
            labs = await self.scan_repository_labs(repo_path, repo_config)
            
            return {
                "success": True,
                "repository": repo_name,
                "action": action,
                "path": str(repo_path),
                "labs_found": len(labs),
                "labs": labs,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error with repository {repo_name}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "action": "error",
                "error": str(e)
            }
    
    async def scan_repository_labs(self, repo_path: Path, repo_config: Dict) -> List[Dict]:
        """Scan a repository for containerlab topology files with enhanced validation and error handling"""
        labs = []
        lab_paths = repo_config.get("lab_paths", ["./"])
        scan_stats = {
            "total_files_found": 0,
            "valid_labs": 0,
            "validation_failures": 0,
            "parse_errors": 0,
            "file_errors": 0
        }
        
        try:
            logger.info(f"Scanning repository {repo_config['name']} for containerlab files...")
            
            for lab_path in lab_paths:
                search_path = repo_path / lab_path.lstrip("./")
                if not search_path.exists():
                    logger.debug(f"Lab path does not exist: {search_path}")
                    continue
                    
                # Find all .clab.yml files with comprehensive search patterns
                lab_patterns = ["*.clab.yml", "*.clab.yaml", "*containerlab.yml", "*containerlab.yaml"]
                
                for pattern in lab_patterns:
                    for lab_file in search_path.rglob(pattern):
                        scan_stats["total_files_found"] += 1
                        
                        try:
                            # Validate file accessibility and size
                            if not self._validate_lab_file_access(lab_file):
                                scan_stats["file_errors"] += 1
                                continue
                            
                            # Parse lab file with enhanced error handling
                            lab_config = await self._parse_lab_file_safe(lab_file)
                            if not lab_config:
                                scan_stats["parse_errors"] += 1
                                continue
                            
                            # Validate lab configuration structure
                            validation_result = self._validate_lab_config(lab_config, lab_file)
                            if not validation_result["valid"]:
                                scan_stats["validation_failures"] += 1
                                logger.debug(f"Lab validation failed for {lab_file}: {validation_result['reason']}")
                                continue
                            
                            # Extract enhanced lab information
                            lab_info = await self._extract_enhanced_lab_info(
                                lab_config, lab_file, repo_path, repo_config, validation_result
                            )
                            
                            if lab_info:
                                labs.append(lab_info)
                                scan_stats["valid_labs"] += 1
                                logger.debug(f"Successfully processed lab: {lab_info['name']} in {lab_info['relative_path']}")
                        
                        except Exception as e:
                            scan_stats["parse_errors"] += 1
                            logger.warning(f"Error processing lab file {lab_file}: {type(e).__name__}: {e}")
                            continue
            
            # Log comprehensive scan results
            logger.info(f"Repository scan complete for {repo_config['name']}: "
                       f"Found {scan_stats['total_files_found']} files, "
                       f"validated {scan_stats['valid_labs']} labs, "
                       f"{scan_stats['validation_failures']} validation failures, "
                       f"{scan_stats['parse_errors']} parse errors, "
                       f"{scan_stats['file_errors']} file access errors")
            
        except Exception as e:
            logger.error(f"Critical error scanning repository {repo_path}: {type(e).__name__}: {e}")
            
        return labs
    
    def _validate_lab_file_access(self, lab_file: Path) -> bool:
        """Validate lab file accessibility and basic properties"""
        try:
            if not lab_file.exists():
                return False
            
            if not lab_file.is_file():
                return False
            
            # Check file size (skip empty files and files > 10MB)
            file_size = lab_file.stat().st_size
            if file_size == 0 or file_size > 10 * 1024 * 1024:
                logger.debug(f"Skipping file due to size: {lab_file} ({file_size} bytes)")
                return False
            
            # Check if file is readable
            with open(lab_file, 'r', encoding='utf-8') as f:
                # Try to read the first line to ensure file is readable
                f.readline()
            
            return True
            
        except Exception as e:
            logger.debug(f"File access validation failed for {lab_file}: {e}")
            return False
    
    async def _parse_lab_file_safe(self, lab_file: Path) -> Optional[Dict]:
        """Safely parse lab file with comprehensive error handling"""
        try:
            with open(lab_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return None
            
            # Parse YAML with safe loader
            lab_config = yaml.safe_load(content)
            
            if not isinstance(lab_config, dict):
                logger.debug(f"Lab file {lab_file} does not contain valid YAML dictionary")
                return None
            
            return lab_config
            
        except yaml.YAMLError as e:
            logger.debug(f"YAML parsing error in {lab_file}: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.debug(f"Unicode decode error in {lab_file}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error parsing {lab_file}: {type(e).__name__}: {e}")
            return None
    
    def _validate_lab_config(self, lab_config: Dict, lab_file: Path) -> Dict:
        """Validate containerlab configuration structure and content"""
        validation_result = {"valid": False, "reason": "", "quality_score": 0, "issues": []}
        
        try:
            # Check for required top-level structure
            if "topology" not in lab_config:
                validation_result["reason"] = "Missing 'topology' section"
                return validation_result
            
            topology = lab_config["topology"]
            if not isinstance(topology, dict):
                validation_result["reason"] = "'topology' is not a dictionary"
                return validation_result
            
            # Validate nodes section
            nodes = topology.get("nodes", {})
            if not isinstance(nodes, dict):
                validation_result["reason"] = "'nodes' is not a dictionary"
                return validation_result
            
            if len(nodes) == 0:
                validation_result["reason"] = "No nodes defined in topology"
                return validation_result
            
            # Validate each node configuration
            valid_nodes = 0
            for node_name, node_config in nodes.items():
                if not isinstance(node_config, dict):
                    validation_result["issues"].append(f"Node '{node_name}' is not a dictionary")
                    continue
                
                # Check for required node properties
                if "kind" not in node_config and "image" not in node_config:
                    validation_result["issues"].append(f"Node '{node_name}' missing both 'kind' and 'image'")
                    continue
                
                valid_nodes += 1
            
            if valid_nodes == 0:
                validation_result["reason"] = "No valid nodes found"
                return validation_result
            
            # Calculate quality score based on various factors
            quality_score = 0
            
            # Basic structure (20 points)
            quality_score += 20
            
            # Lab name defined (10 points)
            if lab_config.get("name"):
                quality_score += 10
            
            # Description provided (10 points)
            if lab_config.get("description") or topology.get("description"):
                quality_score += 10
            
            # Multiple nodes (10 points for 2+, 20 for 5+)
            if valid_nodes >= 5:
                quality_score += 20
            elif valid_nodes >= 2:
                quality_score += 10
            
            # Links defined (15 points)
            if topology.get("links"):
                quality_score += 15
            
            # Management configuration (10 points)
            if topology.get("mgmt"):
                quality_score += 10
            
            # Proper node kinds/images (5 points)
            if any(node.get("kind") for node in nodes.values()):
                quality_score += 5
            
            validation_result["valid"] = True
            validation_result["quality_score"] = quality_score
            validation_result["node_count"] = valid_nodes
            
            return validation_result
            
        except Exception as e:
            validation_result["reason"] = f"Validation error: {type(e).__name__}: {e}"
            return validation_result
    
    async def _extract_enhanced_lab_info(self, lab_config: Dict, lab_file: Path, 
                                        repo_path: Path, repo_config: Dict, 
                                        validation_result: Dict) -> Optional[Dict]:
        """Extract comprehensive lab information with enhanced metadata"""
        try:
            lab_name = lab_config.get("name", lab_file.stem.replace(".clab", ""))
            topology = lab_config.get("topology", {})
            nodes = topology.get("nodes", {})
            
            # Filter and count valid nodes
            valid_nodes = {k: v for k, v in nodes.items() if v is not None and isinstance(v, dict)}
            node_count = len(valid_nodes)
            
            # Enhanced vendor and kind extraction
            kinds, vendors = self._extract_enhanced_node_info(valid_nodes, topology)
            
            # Infer additional metadata
            difficulty = self._infer_lab_difficulty(lab_config, lab_name, node_count, validation_result)
            category = self._infer_lab_category(lab_config, lab_name, kinds, vendors)
            use_cases = self._infer_lab_use_cases(lab_config, lab_name, kinds, vendors)
            
            # Get relative path from repository root
            rel_path = lab_file.relative_to(repo_path)
            
            lab_info = {
                "name": lab_name,
                "file_path": str(lab_file),
                "relative_path": str(rel_path),
                "repository": repo_config["name"],
                "repository_category": repo_config.get("category", "unknown"),
                "repository_vendor": repo_config.get("vendor", "unknown"),
                "description": lab_config.get("description") or topology.get("description") or f"{lab_name} containerlab topology",
                "nodes": node_count,
                "kinds": kinds,
                "vendors": vendors,
                "difficulty": difficulty,
                "category": category,
                "use_cases": use_cases,
                "quality_score": validation_result.get("quality_score", 0),
                "has_links": bool(topology.get("links")),
                "has_mgmt": bool(topology.get("mgmt")),
                "source": "repository",
                "topology": topology,
                "validation_issues": validation_result.get("issues", []),
                "last_scanned": datetime.now().isoformat()
            }
            
            return lab_info
            
        except Exception as e:
            logger.warning(f"Error extracting lab info from {lab_file}: {e}")
            return None
    
    def _extract_enhanced_node_info(self, valid_nodes: Dict, topology: Dict) -> Tuple[List[str], List[str]]:
        """Extract enhanced node kinds and vendor information"""
        kinds = set()
        vendors = set()
        
        # Extract from individual nodes
        for node_name, node_config in valid_nodes.items():
            if isinstance(node_config, dict):
                kind = node_config.get("kind", "").lower()
                image = node_config.get("image", "").lower()
                
                # Add kind
                if kind:
                    kinds.add(kind)
                
                # Enhanced vendor detection
                vendor_patterns = {
                    "nokia": ["nokia", "srl", "sr-linux", "7220", "7250"],
                    "arista": ["arista", "ceos", "eos", "veos"],
                    "cisco": ["cisco", "xr", "ios", "nxos", "cat9k", "csr", "n9k"],
                    "juniper": ["juniper", "vmx", "crpd", "vjunos", "vqfx", "vsrx"],
                    "cumulus": ["cumulus", "nvue", "vx"],
                    "sonic": ["sonic", "azure", "msft"],
                    "frr": ["frr", "frrouting"],
                    "openvswitch": ["openvswitch", "ovs"],
                    "fortinet": ["fortinet", "fortigate"],
                    "paloalto": ["paloalto", "pan"],
                    "dell": ["dell", "os10"],
                    "huawei": ["huawei", "vrp"],
                    "mikrotik": ["mikrotik", "routeros"],
                    "vyos": ["vyos"],
                    "linux": ["linux", "ubuntu", "centos", "alpine", "debian"]
                }
                
                for vendor, patterns in vendor_patterns.items():
                    if any(pattern in image for pattern in patterns):
                        vendors.add(vendor)
                        break
        
        # Use defaults from topology if available
        topology_defaults = topology.get("defaults", {})
        if topology_defaults:
            default_kind = topology_defaults.get("kind")
            if default_kind and not kinds:
                kinds.add(default_kind.lower())
        
        return list(kinds), list(vendors)
    
    def _infer_lab_difficulty(self, lab_config: Dict, lab_name: str, node_count: int, validation_result: Dict) -> str:
        """Infer difficulty level from lab characteristics"""
        lab_name_lower = lab_name.lower()
        topology = lab_config.get("topology", {})
        quality_score = validation_result.get("quality_score", 0)
        
        # Expert level indicators
        expert_keywords = [
            "clos", "datacenter", "fabric", "evpn", "mpls", "sr-", "segment", 
            "telemetry", "automation", "ci/cd", "production", "enterprise"
        ]
        if any(keyword in lab_name_lower for keyword in expert_keywords):
            return "expert"
        
        # Advanced level indicators
        advanced_keywords = [
            "vxlan", "bgp", "ospf", "isis", "multi-vendor", "spine", "leaf",
            "routing", "protocol", "advanced", "complex"
        ]
        if any(keyword in lab_name_lower for keyword in advanced_keywords):
            return "advanced"
        
        # Beginner level indicators
        beginner_keywords = [
            "basic", "simple", "intro", "tutorial", "hello", "getting-started",
            "01", "first", "begin"
        ]
        if any(keyword in lab_name_lower for keyword in beginner_keywords):
            return "beginner"
        
        # Node count based inference
        if node_count >= 10:
            return "expert"
        elif node_count >= 5:
            return "advanced"
        elif node_count <= 2:
            return "beginner"
        
        # Quality score based inference
        if quality_score >= 80:
            return "advanced"
        elif quality_score <= 40:
            return "beginner"
        
        return "intermediate"
    
    def _infer_lab_category(self, lab_config: Dict, lab_name: str, kinds: List[str], vendors: List[str]) -> str:
        """Infer lab category from characteristics"""
        lab_name_lower = lab_name.lower()
        topology = lab_config.get("topology", {})
        
        # Category mapping based on keywords and characteristics
        category_patterns = {
            "security": ["security", "firewall", "pan", "fortigate", "fortinet", "acl", "vpn"],
            "automation": ["automation", "ansible", "python", "api", "netconf", "gnmi", "restconf", "script"],
            "datacenter": ["datacenter", "clos", "fabric", "spine", "leaf", "dc", "data-center"],
            "routing": ["bgp", "ospf", "isis", "routing", "protocol", "rip", "eigrp"],
            "overlay": ["vxlan", "evpn", "overlay", "underlay", "tunnel"],
            "telemetry": ["telemetry", "monitoring", "observability", "grafana", "prometheus", "influx"],
            "kubernetes": ["kubernetes", "k8s", "cni", "pod", "container"],
            "mpls": ["mpls", "segment", "sr-", "srv6", "ldp"],
            "wireless": ["wifi", "wireless", "ap", "controller"],
            "service_provider": ["provider", "isp", "carrier", "transport"],
            "campus": ["campus", "access", "distribution", "core"]
        }
        
        for category, keywords in category_patterns.items():
            if any(keyword in lab_name_lower for keyword in keywords):
                return category
        
        # Multi-vendor determination
        if len(vendors) >= 2:
            return "multi_vendor"
        
        # Single vendor categories
        if "nokia" in vendors:
            return "nokia_specific"
        elif "arista" in vendors:
            return "arista_specific"
        elif "cisco" in vendors:
            return "cisco_specific"
        elif "juniper" in vendors:
            return "juniper_specific"
        
        # Default categories
        if len(kinds) == 1 and "linux" in kinds:
            return "linux_networking"
        
        return "general_networking"
    
    def _infer_lab_use_cases(self, lab_config: Dict, lab_name: str, kinds: List[str], vendors: List[str]) -> List[str]:
        """Infer specific use cases from lab characteristics"""
        lab_name_lower = lab_name.lower()
        topology = lab_config.get("topology", {})
        use_cases = []
        
        # Use case mapping
        use_case_patterns = {
            "getting_started": ["basic", "intro", "hello", "tutorial", "getting-started", "first"],
            "interoperability": ["multi-vendor", "interop", "integration", "compat"],
            "protocol_learning": ["bgp", "ospf", "isis", "protocol", "routing"],
            "datacenter_design": ["datacenter", "clos", "fabric", "spine", "leaf"],
            "network_automation": ["automation", "ansible", "python", "api"],
            "security_testing": ["security", "firewall", "acl", "pen", "test"],
            "telemetry_monitoring": ["telemetry", "monitor", "observ", "grafana"],
            "overlay_networking": ["vxlan", "evpn", "overlay", "tunnel"],
            "kubernetes_networking": ["k8s", "kubernetes", "cni", "pod"],
            "campus_design": ["campus", "access", "distribution"],
            "service_provider": ["provider", "isp", "carrier", "mpls"],
            "troubleshooting": ["debug", "troubleshoot", "problem", "issue"],
            "performance_testing": ["performance", "perf", "benchmark", "load"],
            "configuration_management": ["config", "template", "provision"]
        }
        
        for use_case, keywords in use_case_patterns.items():
            if any(keyword in lab_name_lower for keyword in keywords):
                use_cases.append(use_case)
        
        # Add default use cases if none found
        if not use_cases:
            node_count = len(topology.get("nodes", {}))
            if node_count == 1:
                use_cases.append("single_node_testing")
            elif node_count == 2:
                use_cases.append("point_to_point")
            elif len(vendors) >= 2:
                use_cases.append("multi_vendor_testing")
            else:
                use_cases.append("general_networking")
        
        return use_cases
    
    async def get_all_repositories(self) -> Dict:
        """Get information about all managed repositories"""
        try:
            config = await self.load_or_create_config()
            metadata = await self.load_repositories_metadata()
            
            repositories = []
            # Handle all repository categories
            repo_categories = [
                "core_repositories", 
                "vendor_repositories", 
                "community_repositories", 
                "educational_repositories", 
                "specialty_repositories", 
                "additional_sources"
            ]
            
            for repo_list_name in repo_categories:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    repo_info = {
                        "name": repo_name,
                        "url": repo_config["url"],
                        "branch": repo_config.get("branch", "main"),
                        "category": repo_config.get("category", "unknown"),
                        "vendor": repo_config.get("vendor", "unknown"),
                        "description": repo_config.get("description", ""),
                        "auto_sync": repo_config.get("auto_sync", False),
                        "sync_frequency": repo_config.get("sync_frequency", 86400),
                        "exists": repo_path.exists(),
                        "path": str(repo_path) if repo_path.exists() else None,
                        "metadata": metadata.get(repo_name, {}),
                        "repository_category": repo_list_name
                    }
                    
                    repositories.append(repo_info)
            
            return {
                "success": True,
                "repositories": repositories,
                "total_repositories": len(repositories),
                "config_path": str(self.repositories_config_file),
                "repositories_dir": str(self.repositories_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "repositories": []
            }
    
    async def get_all_labs_from_repositories(self) -> List[Dict]:
        """Get all labs from all managed repositories"""
        all_labs = []
        
        try:
            config = await self.load_or_create_config()
            
            # Handle all repository categories
            repo_categories = [
                "core_repositories", 
                "vendor_repositories", 
                "community_repositories", 
                "educational_repositories", 
                "specialty_repositories", 
                "additional_sources"
            ]
            
            for repo_list_name in repo_categories:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    if repo_path.exists():
                        labs = await self.scan_repository_labs(repo_path, repo_config)
                        all_labs.extend(labs)
            
            logger.info(f"Found {len(all_labs)} labs across all repositories")
            return all_labs
            
        except Exception as e:
            logger.error(f"Error getting labs from repositories: {e}")
            return []
    
    async def sync_repository(self, repo_name: str) -> Dict:
        """Sync a specific repository"""
        try:
            config = await self.load_or_create_config()
            
            # Find repository configuration
            repo_config = None
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo in config.get(repo_list_name, []):
                    if repo["name"] == repo_name:
                        repo_config = repo
                        break
                if repo_config:
                    break
            
            if not repo_config:
                return {
                    "success": False,
                    "error": "Repository not found in configuration",
                    "repository": repo_name
                }
            
            # Perform sync
            result = await self.clone_or_update_repository(repo_config)
            
            # Update sync status
            await self.update_sync_status(repo_name, result["success"])
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return result
            
        except Exception as e:
            logger.error(f"Error syncing repository {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository": repo_name
            }
    
    async def sync_all_repositories(self) -> Dict:
        """Sync all configured repositories"""
        try:
            config = await self.load_or_create_config()
            results = []
            
            # Sync core repositories
            for repo_config in config.get("core_repositories", []):
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
                await self.update_sync_status(repo_config["name"], result["success"])
            
            # Sync additional sources
            for repo_config in config.get("additional_sources", []):
                result = await self.clone_or_update_repository(repo_config)
                results.append(result)
                await self.update_sync_status(repo_config["name"], result["success"])
            
            # Update metadata
            await self.update_repositories_metadata()
            
            successful = sum(1 for r in results if r["success"])
            total = len(results)
            
            return {
                "success": True,
                "message": f"Synced {successful}/{total} repositories",
                "results": results,
                "successful": successful,
                "total": total,
                "last_sync": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing all repositories: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync repositories"
            }
    
    async def add_repository(self, repo_config: Dict) -> Dict:
        """Add a new repository to the configuration"""
        try:
            # Validate repository configuration
            required_fields = ["name", "url"]
            for field in required_fields:
                if field not in repo_config:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Load current configuration
            config = await self.load_or_create_config()
            
            # Check if repository already exists
            repo_name = repo_config["name"]
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for existing_repo in config.get(repo_list_name, []):
                    if existing_repo["name"] == repo_name:
                        return {
                            "success": False,
                            "error": f"Repository {repo_name} already exists"
                        }
            
            # Set defaults
            repo_config.setdefault("branch", "main")
            repo_config.setdefault("category", "custom")
            repo_config.setdefault("description", f"Custom repository: {repo_name}")
            repo_config.setdefault("lab_paths", ["./"])
            repo_config.setdefault("auto_sync", False)
            repo_config.setdefault("sync_frequency", 604800)  # 7 days
            
            # Add to additional sources
            if "additional_sources" not in config:
                config["additional_sources"] = []
            config["additional_sources"].append(repo_config)
            
            # Save configuration
            config["last_updated"] = datetime.now().isoformat()
            async with aiofiles.open(self.repositories_config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            # Clone the repository
            result = await self.clone_or_update_repository(repo_config)
            
            return {
                "success": True,
                "message": f"Repository {repo_name} added successfully",
                "repository": repo_name,
                "clone_result": result
            }
            
        except Exception as e:
            logger.error(f"Error adding repository: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_repository(self, repo_name: str) -> Dict:
        """Remove a repository from the configuration and filesystem"""
        try:
            # Load current configuration
            config = await self.load_or_create_config()
            
            # Find and remove repository from configuration
            found = False
            for repo_list_name in ["core_repositories", "additional_sources"]:
                repo_list = config.get(repo_list_name, [])
                for i, repo in enumerate(repo_list):
                    if repo["name"] == repo_name:
                        del repo_list[i]
                        found = True
                        break
                if found:
                    break
            
            if not found:
                return {
                    "success": False,
                    "error": f"Repository {repo_name} not found in configuration"
                }
            
            # Save updated configuration
            config["last_updated"] = datetime.now().isoformat()
            async with aiofiles.open(self.repositories_config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            # Remove repository directory
            repo_path = self.repositories_dir / repo_name
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logger.info(f"Removed repository directory: {repo_path}")
            
            # Update metadata
            await self.update_repositories_metadata()
            
            return {
                "success": True,
                "message": f"Repository {repo_name} removed successfully",
                "repository": repo_name
            }
            
        except Exception as e:
            logger.error(f"Error removing repository {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "repository": repo_name
            }
    
    async def get_repository_status(self, repo_name: str) -> Dict:
        """Get detailed status of a specific repository"""
        try:
            config = await self.load_or_create_config()
            repo_path = self.repositories_dir / repo_name
            
            # Find repository configuration
            repo_config = None
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo in config.get(repo_list_name, []):
                    if repo["name"] == repo_name:
                        repo_config = repo
                        break
                if repo_config:
                    break
            
            if not repo_config:
                return {
                    "success": False,
                    "error": f"Repository {repo_name} not found in configuration"
                }
            
            status = {
                "name": repo_name,
                "exists": repo_path.exists(),
                "path": str(repo_path),
                "config": repo_config
            }
            
            if repo_path.exists() and (repo_path / ".git").exists():
                # Get git information
                try:
                    # Get current branch
                    process = await asyncio.create_subprocess_exec(
                        "git", "branch", "--show-current",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        status["current_branch"] = stdout.decode().strip()
                    
                    # Get last commit info
                    process = await asyncio.create_subprocess_exec(
                        "git", "log", "-1", "--format=%H|%an|%ad|%s",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        commit_info = stdout.decode().strip().split("|", 3)
                        if len(commit_info) == 4:
                            status["last_commit"] = {
                                "hash": commit_info[0],
                                "author": commit_info[1],
                                "date": commit_info[2],
                                "message": commit_info[3]
                            }
                    
                    # Check if repository is up to date
                    process = await asyncio.create_subprocess_exec(
                        "git", "fetch", "origin",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    process = await asyncio.create_subprocess_exec(
                        "git", "status", "-uno",
                        cwd=repo_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    if process.returncode == 0:
                        git_status = stdout.decode()
                        status["up_to_date"] = "up to date" in git_status
                        status["needs_pull"] = "behind" in git_status
                    
                except Exception as git_error:
                    logger.warning(f"Error getting git info for {repo_name}: {git_error}")
                    status["git_error"] = str(git_error)
                
                # Scan for labs
                labs = await self.scan_repository_labs(repo_path, repo_config)
                status["labs"] = labs
                status["lab_count"] = len(labs)
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting repository status {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_repositories_metadata(self) -> None:
        """Update metadata file with current repository information"""
        try:
            metadata = {}
            config = await self.load_or_create_config()
            
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    repo_name = repo_config["name"]
                    repo_path = self.repositories_dir / repo_name
                    
                    if repo_path.exists():
                        labs = await self.scan_repository_labs(repo_path, repo_config)
                        metadata[repo_name] = {
                            "last_scanned": datetime.now().isoformat(),
                            "lab_count": len(labs),
                            "exists": True,
                            "path": str(repo_path)
                        }
                    else:
                        metadata[repo_name] = {
                            "last_scanned": datetime.now().isoformat(),
                            "lab_count": 0,
                            "exists": False,
                            "path": None
                        }
            
            async with aiofiles.open(self.repositories_metadata_file, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
                
            logger.info("Updated repositories metadata")
            
        except Exception as e:
            logger.error(f"Error updating repositories metadata: {e}")
    
    async def load_repositories_metadata(self) -> Dict:
        """Load repositories metadata"""
        try:
            if self.repositories_metadata_file.exists():
                async with aiofiles.open(self.repositories_metadata_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return {}
        except Exception as e:
            logger.error(f"Error loading repositories metadata: {e}")
            return {}
    
    async def update_sync_status(self, repo_name: str, success: bool) -> None:
        """Update sync status for a repository"""
        try:
            status = {}
            if self.sync_status_file.exists():
                async with aiofiles.open(self.sync_status_file, 'r') as f:
                    content = await f.read()
                    status = json.loads(content)
            
            status[repo_name] = {
                "last_sync": datetime.now().isoformat(),
                "success": success,
                "sync_count": status.get(repo_name, {}).get("sync_count", 0) + 1
            }
            
            async with aiofiles.open(self.sync_status_file, 'w') as f:
                await f.write(json.dumps(status, indent=2))
                
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    async def get_sync_status(self) -> Dict:
        """Get sync status for all repositories"""
        try:
            if self.sync_status_file.exists():
                async with aiofiles.open(self.sync_status_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return {}
        except Exception as e:
            logger.error(f"Error loading sync status: {e}")
            return {}
    
    async def auto_sync_repositories(self) -> Dict:
        """Perform automatic sync for repositories that have auto_sync enabled"""
        try:
            config = await self.load_or_create_config()
            sync_status = await self.get_sync_status()
            results = []
            
            for repo_list_name in ["core_repositories", "additional_sources"]:
                for repo_config in config.get(repo_list_name, []):
                    if not repo_config.get("auto_sync", False):
                        continue
                    
                    repo_name = repo_config["name"]
                    sync_frequency = repo_config.get("sync_frequency", 86400)  # Default 24 hours
                    
                    # Check if sync is needed
                    last_sync = sync_status.get(repo_name, {}).get("last_sync")
                    if last_sync:
                        last_sync_time = datetime.fromisoformat(last_sync)
                        if datetime.now() - last_sync_time < timedelta(seconds=sync_frequency):
                            continue  # Too soon to sync
                    
                    # Perform sync
                    logger.info(f"Auto-syncing repository: {repo_name}")
                    result = await self.sync_repository(repo_name)
                    results.append(result)
            
            return {
                "success": True,
                "message": f"Auto-sync completed for {len(results)} repositories",
                "results": results,
                "synced_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in auto-sync: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Auto-sync failed"
            }
    
    async def start_background_sync(self):
        """Start the background sync scheduler"""
        if self._scheduler_started:
            logger.info("Background sync scheduler already started")
            return
        
        try:
            self.scheduler = AsyncIOScheduler()
            
            # Schedule auto-sync to run every 5 minutes to check if any repositories need syncing
            self.scheduler.add_job(
                self._background_sync_check,
                IntervalTrigger(minutes=5),
                id='auto_sync_check',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            
            self.scheduler.start()
            self._scheduler_started = True
            logger.info("Background sync scheduler started - will check for sync needs every 5 minutes")
            
        except Exception as e:
            logger.error(f"Error starting background sync scheduler: {e}")
    
    async def stop_background_sync(self):
        """Stop the background sync scheduler"""
        if self.scheduler and self._scheduler_started:
            try:
                self.scheduler.shutdown()
                self._scheduler_started = False
                logger.info("Background sync scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping background sync scheduler: {e}")
    
    async def _background_sync_check(self):
        """Background task that checks if repositories need syncing based on their auto_sync and sync_frequency settings"""
        try:
            logger.debug("Running background sync check...")
            result = await self.auto_sync_repositories()
            
            if result["success"] and result.get("synced_count", 0) > 0:
                logger.info(f"Background sync completed: {result['synced_count']} repositories synced")
            elif not result["success"]:
                logger.error(f"Background sync failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in background sync check: {e}")
    
    def get_scheduler_status(self) -> Dict:
        """Get the current status of the background sync scheduler"""
        next_sync_check = None
        if self.scheduler:
            try:
                job = self.scheduler.get_job('auto_sync_check')
                if job and job.next_run_time:
                    next_sync_check = job.next_run_time.isoformat()
            except Exception:
                next_sync_check = None
                
        return {
            "scheduler_running": self._scheduler_started,
            "scheduler_active": self.scheduler is not None and self.scheduler.running if self.scheduler else False,
            "next_sync_check": next_sync_check
        }
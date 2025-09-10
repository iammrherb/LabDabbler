import asyncio
import aiohttp
import json
import yaml
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class GitHubLabScanner:
    """Service to scan GitHub repositories for containerlab and network labs"""
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.labs_file = self.data_dir / "github_labs.json"
        
        # Known repositories with containerlab topologies
        self.target_repos = [
            "srl-labs/containerlab",
            "networkop/containerlab",
            "hellt/containerlab-examples", 
            "srl-labs/learn-srlinux",
            "aristanetworks/avd-containers-demo",
            "cisco-open/containerlab-networking",
            "juniper/containerlab-examples",
            "nokia/srlinux-labs"
        ]
        
    async def scan_all_repos(self) -> Dict:
        """Scan all target repositories for lab definitions"""
        logger.info("Starting GitHub lab repository scan...")
        
        all_labs = {}
        
        async with aiohttp.ClientSession() as session:
            for repo in self.target_repos:
                try:
                    repo_labs = await self.scan_repository(session, repo)
                    if repo_labs:
                        all_labs[repo] = repo_labs
                        logger.info(f"Found {len(repo_labs)} labs in {repo}")
                except Exception as e:
                    logger.error(f"Failed to scan repository {repo}: {e}")
        
        # Save results
        scan_results = {
            "repositories": all_labs,
            "total_labs": sum(len(labs) for labs in all_labs.values()),
            "last_scan": str(asyncio.get_event_loop().time())
        }
        
        with open(self.labs_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
            
        logger.info(f"Repository scan complete. Found {scan_results['total_labs']} total labs")
        return scan_results
    
    async def scan_repository(self, session: aiohttp.ClientSession, repo: str) -> List[Dict]:
        """Scan a single repository for containerlab files"""
        labs = []
        
        try:
            # Search for .clab.yml files
            search_url = f"https://api.github.com/search/code"
            params = {
                "q": f"filename:.clab.yml repo:{repo}",
                "per_page": 100
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get("items", []):
                        lab_info = await self.parse_lab_file(session, item)
                        if lab_info:
                            labs.append(lab_info)
                            
        except Exception as e:
            logger.error(f"Error scanning repository {repo}: {e}")
            
        return labs
    
    async def parse_lab_file(self, session: aiohttp.ClientSession, file_item: Dict) -> Optional[Dict]:
        """Parse a containerlab file and extract lab information"""
        try:
            # Get file content
            download_url = file_item.get("download_url")
            if not download_url:
                return None
                
            async with session.get(download_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse YAML
                    try:
                        lab_config = yaml.safe_load(content)
                    except yaml.YAMLError:
                        return None
                    
                    # Extract lab information
                    lab_info = {
                        "name": file_item.get("name", "").replace(".clab.yml", ""),
                        "path": file_item.get("path", ""),
                        "repository": file_item.get("repository", {}).get("full_name", ""),
                        "html_url": file_item.get("html_url", ""),
                        "download_url": download_url,
                        "description": self.extract_description(lab_config),
                        "topology": self.extract_topology_info(lab_config),
                        "nodes": self.count_nodes(lab_config),
                        "kinds": self.extract_kinds(lab_config)
                    }
                    
                    return lab_info
                    
        except Exception as e:
            logger.error(f"Error parsing lab file {file_item.get('name', 'unknown')}: {e}")
            
        return None
    
    def extract_description(self, config: Dict) -> str:
        """Extract description from lab config"""
        if isinstance(config, dict):
            # Look for description in various places
            desc = config.get("description", "")
            if not desc and "topology" in config:
                desc = config["topology"].get("description", "")
            if not desc and "name" in config:
                desc = f"Containerlab topology: {config['name']}"
        return desc or "Containerlab network topology"
    
    def extract_topology_info(self, config: Dict) -> Dict:
        """Extract topology information"""
        if not isinstance(config, dict) or "topology" not in config:
            return {}
            
        topology = config["topology"]
        return {
            "name": topology.get("name", ""),
            "kinds": list(topology.get("kinds", {}).keys()),
            "defaults": topology.get("defaults", {}),
            "mgmt": topology.get("mgmt", {})
        }
    
    def count_nodes(self, config: Dict) -> int:
        """Count nodes in the topology"""
        if isinstance(config, dict) and "topology" in config:
            nodes = config["topology"].get("nodes", {})
            return len(nodes) if isinstance(nodes, dict) else 0
        return 0
    
    def extract_kinds(self, config: Dict) -> List[str]:
        """Extract unique node kinds from topology"""
        kinds = set()
        
        if isinstance(config, dict) and "topology" in config:
            topology = config["topology"]
            
            # From kinds section
            if "kinds" in topology:
                kinds.update(topology["kinds"].keys())
            
            # From nodes
            nodes = topology.get("nodes", {})
            if isinstance(nodes, dict):
                for node in nodes.values():
                    if isinstance(node, dict) and "kind" in node:
                        kinds.add(node["kind"])
                        
        return list(kinds)
    
    def load_labs(self) -> Dict:
        """Load labs from file"""
        if self.labs_file.exists():
            with open(self.labs_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def refresh_labs(self) -> Dict:
        """Refresh lab scanning"""
        return await self.scan_all_repos()
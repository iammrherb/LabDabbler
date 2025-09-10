import asyncio
import aiohttp
import json
import yaml
import os
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
        
        # Optional GitHub token for authenticated requests (avoids rate limiting)
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Target organizations and repositories to scan automatically
        self.target_organizations = [
            "networkop",
            "srl-labs", 
            "hellt",
            "PacketAnglers"
        ]
        
        self.target_repositories = [
            "srl-labs/containerlab",
            "hellt/clabs",
            "PacketAnglers/clab-topos",
            "ttafsir/instruqt-clab-topologies",
            "hellt/clab-config-demo",
            "srl-labs/learn-srlinux"
        ]
        
        # Curated list of known containerlab topologies that we can fetch directly
        # This avoids GitHub API authentication issues while providing immediate value
        self.known_labs = [
            # Basic SR Linux examples from main containerlab repo
            {
                "name": "srl01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srl01/srl01.clab.yml",
                "description": "Basic SR Linux lab - single node setup"
            },
            {
                "name": "srl02",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srl02/srl02.clab.yml",
                "description": "SR Linux lab - two node topology"
            },
            {
                "name": "srl03",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srl03/srl03.clab.yml",
                "description": "SR Linux lab - three node topology"
            },
            {
                "name": "srlceos01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srlceos01/srlceos01.clab.yml",
                "description": "SR Linux + Arista cEOS multi-vendor topology"
            },
            {
                "name": "srlfrr01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srlfrr01/srlfrr01.clab.yml",
                "description": "SR Linux + FRRouting topology"
            },
            {
                "name": "srlxrd01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/srlxrd01/srlxrd01.clab.yml",
                "description": "SR Linux + Cisco XRd topology"
            },
            # CLOS topologies
            {
                "name": "clos01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/clos01/clos01.clab.yml",
                "description": "CLOS data center topology #1"
            },
            {
                "name": "clos02",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/clos02/clos02.clab.yml",
                "description": "CLOS data center topology #2"
            },
            # Other vendor examples
            {
                "name": "frr01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/frr01/frr01.clab.yml",
                "description": "FRRouting containerlab topology"
            },
            {
                "name": "sonic01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/sonic01/sonic01.clab.yml",
                "description": "SONiC network operating system lab"
            },
            # Community labs from hellt/clabs (verified working paths)
            {
                "name": "vxlan01",
                "repo": "hellt/clabs",
                "path": "labs/vxlan01/vxlan01.clab.yml",
                "description": "VXLAN lab with SR Linux"
            },
            {
                "name": "2tier-l3ls",
                "repo": "hellt/clabs",
                "path": "labs/2tier-l3ls/2tier-l3ls.clab.yml",
                "description": "Two-tier L3 Leaf-Spine topology"
            },
            # Community labs from PacketAnglers/clab-topos (verified working paths)
            {
                "name": "atd-dc",
                "repo": "PacketAnglers/clab-topos",
                "path": "atd-dc/atd-dc.yml",
                "description": "Arista Test Drive Datacenter topology"
            },
            # Known networkop organization labs
            {
                "name": "k8s-multicast",
                "repo": "networkop/k8s-multicast",
                "path": "clab/k8s-multicast.clab.yml",
                "description": "Kubernetes multicast networking lab with networkop containers"
            },
            {
                "name": "meshnet-cni",
                "repo": "networkop/meshnet-cni",
                "path": "examples/3-node/3-node.clab.yml",
                "description": "3-node meshnet CNI example topology"
            },
            {
                "name": "arista-network-ci",
                "repo": "networkop/arista-network-ci",
                "path": "topo.clab.yml",
                "description": "Arista network CI/CD pipeline example"
            },
            # Networkop-related labs using networkop images
            {
                "name": "cvx01",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/cvx01/cvx01.clab.yml",
                "description": "Cumulus VX with FRRouting - uses networkop/cx:4.3.0 container image"
            },
            {
                "name": "cvx02",
                "repo": "srl-labs/containerlab",
                "path": "lab-examples/cvx02/cvx02.clab.yml",
                "description": "Cumulus VX with Linux host - uses networkop/cx:4.3.0 and networkop/host:ifreload images"
            }
        ]
        
    async def scan_all_repos(self) -> Dict:
        """Comprehensive GitHub lab collection from both curated and automated sources"""
        logger.info("Starting comprehensive GitHub lab collection...")
        
        all_labs = {}
        failed_labs = []
        scan_stats = {
            "curated_labs": 0,
            "automated_labs": 0,
            "failed_repos": []
        }
        
        headers = self._get_auth_headers()
        
        async with aiohttp.ClientSession(headers=headers) as session:
            # Phase 1: Fetch curated/known labs (fast, reliable)
            logger.info("Phase 1: Fetching curated labs...")
            for lab_def in self.known_labs:
                try:
                    lab_info = await self.fetch_known_lab(session, lab_def)
                    if lab_info:
                        repo_name = lab_def["repo"]
                        if repo_name not in all_labs:
                            all_labs[repo_name] = []
                        all_labs[repo_name].append(lab_info)
                        scan_stats["curated_labs"] += 1
                        logger.info(f"Successfully loaded curated lab: {lab_info['name']}")
                    else:
                        failed_labs.append(lab_def["name"])
                        logger.warning(f"Failed to load curated lab: {lab_def['name']}")
                except Exception as e:
                    failed_labs.append(lab_def["name"])
                    logger.error(f"Error loading curated lab {lab_def['name']}: {e}")
                    
                # Small delay to be respectful to GitHub 
                await asyncio.sleep(0.1)
            
            # Phase 2: Search API scanning for organizations
            logger.info("Phase 2: Scanning organizations using GitHub Search API...")
            for org in self.target_organizations:
                try:
                    logger.info(f"Searching for .clab.yml files in organization: {org}")
                    org_labs = await self.search_organization_labs(session, org)
                    
                    if org_labs:
                        # Group by repository
                        for lab in org_labs:
                            repo_name = lab["repository"]
                            if repo_name not in all_labs:
                                all_labs[repo_name] = []
                            
                            # Avoid duplicates from curated list
                            existing_names = {lab_item['name'] for lab_item in all_labs[repo_name]}
                            if lab['name'] not in existing_names:
                                all_labs[repo_name].append(lab)
                                scan_stats["automated_labs"] += 1
                        
                        logger.info(f"Found {len(org_labs)} labs in organization {org}")
                    else:
                        logger.warning(f"No labs found in organization: {org}")
                        
                except Exception as e:
                    scan_stats["failed_repos"].append(f"org:{org}")
                    logger.error(f"Failed to scan organization {org}: {e}")
                    
                # Longer delay between organizations to respect rate limits
                await asyncio.sleep(1.0)
                
            # Phase 3: Fallback repository scanning for specific repos
            logger.info("Phase 3: Fallback repository scanning...")
            for repo in self.target_repositories:
                try:
                    logger.info(f"Searching repository: {repo}")
                    repo_labs = await self.search_repository_labs(session, repo)
                    
                    if repo_labs:
                        if repo not in all_labs:
                            all_labs[repo] = []
                        # Avoid duplicates from curated list and org scanning
                        existing_names = {lab['name'] for lab in all_labs[repo]}
                        for lab in repo_labs:
                            if lab['name'] not in existing_names:
                                all_labs[repo].append(lab)
                                scan_stats["automated_labs"] += 1
                        logger.info(f"Found {len(repo_labs)} additional labs in {repo}")
                    else:
                        logger.warning(f"No labs found in repository: {repo}")
                        
                except Exception as e:
                    scan_stats["failed_repos"].append(repo)
                    logger.error(f"Failed to scan repository {repo}: {e}")
                    
                # Delay between repositories to respect rate limits
                await asyncio.sleep(0.5)
        
        # Save comprehensive results with rate limit info
        rate_limited = len([repo for repo in scan_stats["failed_repos"] if "rate limited" in str(repo)]) > 0
        
        scan_results = {
            "repositories": all_labs,
            "total_labs": sum(len(labs) for labs in all_labs.values()),
            "curated_labs": scan_stats["curated_labs"],
            "automated_labs": scan_stats["automated_labs"],
            "failed_labs": failed_labs,
            "failed_repos": scan_stats["failed_repos"],
            "last_scan": str(asyncio.get_event_loop().time()),
            "scan_method": "hybrid_curated_and_automated",
            "rate_limited": rate_limited,
            "github_token_configured": bool(self.github_token),
            "notes": self._generate_scan_notes(rate_limited, scan_stats)
        }
        
        with open(self.labs_file, 'w') as f:
            json.dump(scan_results, f, indent=2)
            
        logger.info(f"Comprehensive lab collection complete. Total: {scan_results['total_labs']} labs "
                   f"({scan_stats['curated_labs']} curated + {scan_stats['automated_labs']} automated)")
        
        if rate_limited:
            logger.warning("GitHub rate limiting encountered. Consider adding GITHUB_TOKEN environment variable for better results.")
            
        return scan_results
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'LabDabbler/1.0'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        return headers
    
    async def fetch_known_lab(self, session: aiohttp.ClientSession, lab_def: Dict) -> Optional[Dict]:
        """Fetch a specific known lab definition"""
        try:
            repo = lab_def["repo"]
            path = lab_def["path"]
            
            # Try main branch first, then master
            for branch in ["main", "master"]:
                raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
                
                async with session.get(raw_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse YAML content
                        try:
                            lab_config = yaml.safe_load(content)
                        except yaml.YAMLError as e:
                            logger.warning(f"Failed to parse YAML for {lab_def['name']}: {e}")
                            continue
                        
                        # Create lab info
                        lab_info = {
                            "name": lab_def["name"],
                            "path": path,
                            "file_path": raw_url,  # Use raw URL for launching
                            "repository": repo,
                            "html_url": f"https://github.com/{repo}/blob/{branch}/{path}",
                            "download_url": raw_url,
                            "description": lab_def.get("description", self.extract_description(lab_config)),
                            "topology": self.extract_topology_info(lab_config),
                            "nodes": self.count_nodes(lab_config),
                            "kinds": self.extract_kinds(lab_config),
                            "source": "github"
                        }
                        
                        return lab_info
                        
                    elif response.status == 404 and branch == "main":
                        # Try master branch next
                        continue
                    else:
                        logger.warning(f"Failed to fetch {lab_def['name']} from {branch} branch (status: {response.status})")
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching known lab {lab_def['name']}: {e}")
            
        return None
    
    async def search_organization_labs(self, session: aiohttp.ClientSession, org: str) -> List[Dict]:
        """Use GitHub Search API to find .clab.yml files in an organization"""
        labs = []
        
        try:
            # Use GitHub Search API to find all .clab.yml files in the organization
            search_query = f"filename:.clab.yml org:{org}"
            search_url = "https://api.github.com/search/code"
            
            page = 1
            max_pages = 10  # Limit to prevent excessive API calls
            
            while page <= max_pages:
                params = {
                    "q": search_query,
                    "per_page": 30,  # Max allowed by GitHub
                    "page": page
                }
                
                logger.info(f"Searching {org} organization, page {page}...")
                
                # Implement retry logic with exponential backoff
                search_results = await self._search_with_retry(session, search_url, params)
                
                if not search_results:
                    break
                    
                items = search_results.get("items", [])
                if not items:
                    logger.info(f"No more results found for {org} on page {page}")
                    break
                
                # Process each found file
                for item in items:
                    try:
                        lab_info = await self.parse_search_result(session, item)
                        if lab_info:
                            labs.append(lab_info)
                            logger.info(f"Found lab: {lab_info['name']} in {lab_info['repository']}")
                    except Exception as item_error:
                        logger.warning(f"Failed to parse search result: {item_error}")
                
                # Check if we've reached the last page
                total_count = search_results.get("total_count", 0)
                if len(items) < 30 or (page * 30) >= total_count:
                    break
                    
                page += 1
                
                # Rate limiting delay between pages
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error searching organization {org}: {e}")
            
        return labs
    
    async def search_repository_labs(self, session: aiohttp.ClientSession, repo: str) -> List[Dict]:
        """Use GitHub Search API to find .clab.yml files in a specific repository"""
        labs = []
        
        try:
            # Use GitHub Search API to find all .clab.yml files in the repository
            search_query = f"filename:.clab.yml repo:{repo}"
            search_url = "https://api.github.com/search/code"
            
            params = {
                "q": search_query,
                "per_page": 100  # Max allowed by GitHub
            }
            
            logger.info(f"Searching repository {repo}...")
            
            # Implement retry logic with exponential backoff
            search_results = await self._search_with_retry(session, search_url, params)
            
            if search_results:
                items = search_results.get("items", [])
                logger.info(f"Found {len(items)} .clab.yml files in {repo}")
                
                # Process each found file
                for item in items:
                    try:
                        lab_info = await self.parse_search_result(session, item)
                        if lab_info:
                            labs.append(lab_info)
                            logger.info(f"Parsed lab: {lab_info['name']}")
                    except Exception as item_error:
                        logger.warning(f"Failed to parse search result: {item_error}")
            else:
                logger.warning(f"No search results for {repo}")
                
        except Exception as e:
            logger.error(f"Error searching repository {repo}: {e}")
            
        return labs
    
    async def scan_repository_contents(self, session: aiohttp.ClientSession, repo: str, path: str = "", depth: int = 0) -> List[Dict]:
        """Recursively scan repository contents for .clab.yml files with proper error handling"""
        labs = []
        
        # Limit recursion depth to prevent infinite loops and reduce API calls
        if depth > 4:
            logger.debug(f"Max depth reached for {repo}/{path}")
            return labs
        
        try:
            # Get contents of current directory
            contents_url = f"https://api.github.com/repos/{repo}/contents/{path}"
            
            # Implement retry logic for rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with session.get(contents_url) as response:
                        if response.status == 200:
                            contents = await response.json()
                            
                            # Handle both file and directory listings
                            if isinstance(contents, list):
                                for item in contents:
                                    await self.process_content_item(session, repo, item, labs, depth)
                            else:
                                # Single file response
                                await self.process_content_item(session, repo, contents, labs, depth)
                            break
                            
                        elif response.status == 403:
                            # Check if it's rate limiting
                            reset_time = response.headers.get('X-RateLimit-Reset')
                            if reset_time:
                                logger.warning(f"Rate limited for {repo}/{path}. Reset at: {reset_time}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(min(60, 2 ** attempt))  # Exponential backoff
                                    continue
                            else:
                                logger.warning(f"Access denied for {repo}/{path}")
                            break
                            
                        elif response.status == 404:
                            logger.debug(f"Path not found: {repo}/{path}")
                            break
                            
                        elif response.status == 422:
                            logger.warning(f"Repository {repo} is too large or has issues")
                            break
                            
                        else:
                            logger.warning(f"HTTP {response.status} for {repo}/{path}")
                            if attempt < max_retries - 1 and response.status >= 500:
                                await asyncio.sleep(2 ** attempt)  # Retry on server errors
                                continue
                            break
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout accessing {repo}/{path} (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    break
                except Exception as e:
                    logger.error(f"Request error for {repo}/{path}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error scanning contents for {repo}{path}: {e}")
            
        return labs
    
    async def process_content_item(self, session: aiohttp.ClientSession, repo: str, item: Dict, labs: List[Dict], depth: int = 0):
        """Process a single content item (file or directory) with error handling"""
        try:
            item_name = item.get("name", "")
            item_type = item.get("type", "")
            item_path = item.get("path", "")
            
            if item_type == "file" and item_name.endswith(".clab.yml"):
                # Found a containerlab file
                logger.info(f"Found .clab.yml file: {item_path} in {repo}")
                
                # Create a mock file_item for parse_lab_file compatibility
                file_item = {
                    "name": item_name,
                    "path": item_path,
                    "repository": {"full_name": repo},
                    "html_url": item.get("html_url", "")
                }
                
                lab_info = await self.parse_lab_file(session, file_item)
                if lab_info:
                    labs.append(lab_info)
                    logger.info(f"Successfully parsed lab: {lab_info['name']}")
                    
            elif item_type == "dir":
                # Recursively scan subdirectories with depth control
                if depth < 4:  # Limit recursion depth
                    try:
                        sublabs = await self.scan_repository_contents(session, repo, item_path, depth + 1)
                        labs.extend(sublabs)
                    except Exception as subdir_error:
                        logger.warning(f"Failed to scan subdirectory {item_path} in {repo}: {subdir_error}")
                    
                    # Small delay between subdirectory scans
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error processing content item {item.get('name', 'unknown')} in {repo}: {e}")
    
    async def parse_lab_file(self, session: aiohttp.ClientSession, file_item: Dict) -> Optional[Dict]:
        """Parse a containerlab file and extract lab information with robust error handling"""
        try:
            # Construct raw file URL from repository info and path
            repo = file_item.get("repository", {})
            repo_name = repo.get("full_name", "")
            file_path = file_item.get("path", "")
            
            if not repo_name or not file_path:
                logger.warning(f"Missing repository name or file path for {file_item.get('name', 'unknown')}")
                return None
                
            # Try main branch first, then master if main fails
            for branch in ["main", "master"]:
                branch_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
                
                # Implement retry logic for file downloads
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        async with session.get(branch_url) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Validate content is not empty
                                if not content.strip():
                                    logger.warning(f"Empty file: {file_path} from {repo_name}")
                                    break
                                
                                # Parse YAML with error handling
                                try:
                                    lab_config = yaml.safe_load(content)
                                    if lab_config is None:
                                        logger.warning(f"File contains no valid YAML: {file_path} from {repo_name}")
                                        break
                                except yaml.YAMLError as e:
                                    logger.warning(f"Failed to parse YAML for {file_item.get('name', 'unknown')}: {e}")
                                    break
                                
                                # Validate basic lab structure
                                if not isinstance(lab_config, dict):
                                    logger.warning(f"Invalid lab config structure in {file_path} from {repo_name}")
                                    break
                                
                                # Extract lab information with safe defaults
                                lab_info = {
                                    "name": file_item.get("name", "").replace(".clab.yml", ""),
                                    "path": file_path,
                                    "file_path": branch_url,  # Use the raw URL as file_path for launching
                                    "repository": repo_name,
                                    "html_url": file_item.get("html_url", ""),
                                    "download_url": branch_url,
                                    "description": self.extract_description(lab_config),
                                    "topology": self.extract_topology_info(lab_config),
                                    "nodes": self.count_nodes(lab_config),
                                    "kinds": self.extract_kinds(lab_config),
                                    "source": "github"
                                }
                                
                                return lab_info
                                
                            elif response.status == 404 and branch == "main":
                                # Try master branch next
                                break
                            elif response.status == 403:
                                logger.warning(f"Rate limited while fetching {file_path} from {repo_name}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(1)
                                    continue
                                break
                            else:
                                logger.warning(f"HTTP {response.status} fetching {file_path} from {repo_name}")
                                break
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout fetching {file_path} from {repo_name} (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        break
                    except Exception as request_error:
                        logger.error(f"Request error fetching {file_path} from {repo_name}: {request_error}")
                        break
                        
        except Exception as e:
            logger.error(f"Error parsing lab file {file_item.get('name', 'unknown')}: {e}")
            
        return None
    
    async def _search_with_retry(self, session: aiohttp.ClientSession, url: str, params: Dict) -> Optional[Dict]:
        """Execute GitHub Search API request with proper retry logic and rate limiting"""
        max_retries = 5
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 403:
                        # Rate limited - check if we have rate limit info
                        remaining = response.headers.get('X-RateLimit-Remaining', '0')
                        reset_time = response.headers.get('X-RateLimit-Reset')
                        
                        if remaining == '0' and reset_time:
                            # We're rate limited, wait until reset
                            import time
                            reset_timestamp = int(reset_time)
                            current_time = int(time.time())
                            wait_time = max(0, reset_timestamp - current_time + 5)  # Add 5 second buffer
                            
                            logger.warning(f"Rate limited. Reset in {wait_time} seconds. {'Consider adding GITHUB_TOKEN for higher limits.' if not self.github_token else ''}")
                            if wait_time > 120:  # Don't wait more than 2 minutes for automated scanning
                                logger.info(f"Rate limit reset time too long ({wait_time}s), skipping automated search")
                                return None
                            
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Other 403 error (maybe secondary rate limit)
                            wait_time = base_delay * (2 ** attempt)
                            logger.warning(f"403 error, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    elif response.status == 422:
                        # Unprocessable entity - usually means search query is malformed
                        logger.error(f"Search query error (422): {params}")
                        return None
                    
                    elif response.status >= 500:
                        # Server error - retry with exponential backoff
                        wait_time = base_delay * (2 ** attempt)
                        logger.warning(f"Server error {response.status}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        logger.error(f"Unexpected status code {response.status} for search request")
                        return None
                        
            except asyncio.TimeoutError:
                wait_time = base_delay * (2 ** attempt)
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                logger.error(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
        
        logger.error(f"Failed to complete search request after {max_retries} attempts")
        return None
    
    async def parse_search_result(self, session: aiohttp.ClientSession, item: Dict) -> Optional[Dict]:
        """Parse a GitHub Search API result item into lab information"""
        try:
            # Extract information from search result
            file_name = item.get("name", "")
            file_path = item.get("path", "")
            repository = item.get("repository", {})
            repo_name = repository.get("full_name", "")
            html_url = item.get("html_url", "")
            
            if not file_name.endswith(".clab.yml") or not repo_name:
                return None
            
            # Get the raw file content
            download_url = item.get("download_url")
            if not download_url:
                # Construct raw URL if not provided
                download_url = f"https://raw.githubusercontent.com/{repo_name}/main/{file_path}"
            
            # Download and parse the lab file
            lab_config = await self._download_and_parse_lab(session, download_url, repo_name, file_path)
            
            if not lab_config:
                return None
            
            # Create lab info
            lab_name = file_name.replace(".clab.yml", "")
            
            lab_info = {
                "name": lab_name,
                "path": file_path,
                "file_path": download_url,
                "repository": repo_name,
                "html_url": html_url,
                "download_url": download_url,
                "description": self.extract_description(lab_config),
                "topology": self.extract_topology_info(lab_config),
                "nodes": self.count_nodes(lab_config),
                "kinds": self.extract_kinds(lab_config),
                "source": "github_search"
            }
            
            return lab_info
            
        except Exception as e:
            logger.error(f"Error parsing search result: {e}")
            return None
    
    async def _download_and_parse_lab(self, session: aiohttp.ClientSession, download_url: str, repo_name: str, file_path: str) -> Optional[Dict]:
        """Download and parse a lab file with proper error handling and branch fallback"""
        # Try main branch first, then master
        branches = ["main", "master"]
        
        for branch in branches:
            try:
                # Construct the raw URL for this branch
                branch_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
                
                async with session.get(branch_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if not content.strip():
                            logger.warning(f"Empty file: {file_path} from {repo_name}")
                            continue
                        
                        try:
                            lab_config = yaml.safe_load(content)
                            if lab_config and isinstance(lab_config, dict):
                                return lab_config
                        except yaml.YAMLError as e:
                            logger.warning(f"YAML parse error for {file_path}: {e}")
                            continue
                    
                    elif response.status == 404 and branch == "main":
                        # Try master branch
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {file_path} on {branch} branch")
                        
            except Exception as e:
                logger.warning(f"Error downloading {file_path} from {branch} branch: {e}")
                continue
        
        logger.warning(f"Failed to download and parse {file_path} from {repo_name}")
        return None
    
    # Legacy method - keeping for backward compatibility  
    async def scan_repository(self, session: aiohttp.ClientSession, repo: str) -> List[Dict]:
        """Legacy method - replaced by search_repository_labs for better performance"""
        logger.info(f"Using legacy scan method for {repo} - consider using search_repository_labs instead")
        return await self.search_repository_labs(session, repo)
    
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
    
    def _generate_scan_notes(self, rate_limited: bool, scan_stats: Dict) -> List[str]:
        """Generate helpful notes about the scan results"""
        notes = []
        
        if rate_limited:
            notes.append("GitHub API rate limiting encountered. Add GITHUB_TOKEN environment variable for 5000 requests/hour.")
            notes.append("Without authentication, only 60 requests/hour are allowed and may be shared across users.")
            
        if scan_stats["curated_labs"] > 0 and scan_stats["automated_labs"] == 0:
            notes.append("Only curated labs were loaded. Automated scanning was limited by rate limits or API issues.")
            
        if len(scan_stats["failed_repos"]) > 0:
            notes.append(f"Some repositories could not be scanned: {len(scan_stats['failed_repos'])} failed")
            
        return notes
    
    async def refresh_labs(self) -> Dict:
        """Refresh lab scanning"""
        return await self.scan_all_repos()
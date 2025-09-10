from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml
import json
import logging
from pathlib import Path
from services.container_discovery import ContainerDiscoveryService
from services.github_lab_scanner import GitHubLabScanner
from services.lab_launcher import LabLauncherService

logger = logging.getLogger(__name__)

app = FastAPI(title="LabDabbler - Master Lab Repository", version="1.0.0")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage - paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = PROJECT_ROOT / "labs"
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"

# Paths configured successfully

# Initialize services
container_service = ContainerDiscoveryService(DATA_DIR)
lab_scanner = GitHubLabScanner(DATA_DIR)
lab_launcher = LabLauncherService(DATA_DIR)

@app.get("/")
async def root():
    return {"message": "LabDabbler Master Lab Repository API", "version": "1.0.0"}

@app.get("/api/labs")
async def get_labs(include_github: bool = True):
    """Get all available labs with their .clab.yml file paths"""
    labs = []
    
    # Local labs from filesystem - now look for actual .clab.yml files
    if LABS_DIR.exists():
        for category in LABS_DIR.iterdir():
            if category.is_dir():
                category_labs = {
                    "category": category.name,
                    "source": "local",
                    "labs": []
                }
                
                # Look for .clab.yml files in this category
                for lab_file in category.rglob("*.clab.yml"):
                    try:
                        # Load the lab file to get metadata
                        with open(lab_file, 'r') as f:
                            lab_config = yaml.safe_load(f)
                        
                        lab_name = lab_config.get("name", lab_file.stem.replace(".clab", ""))
                        node_count = len(lab_config.get("topology", {}).get("nodes", {}))
                        
                        # Extract node kinds if available
                        nodes = lab_config.get("topology", {}).get("nodes", {})
                        kinds = list(set(node.get("kind", "unknown") for node in nodes.values()))
                        
                        lab_info = {
                            "name": lab_name,
                            "file_path": str(lab_file),  # Use absolute path for now
                            "description": f"{category.name.title()} lab: {lab_name}",
                            "source": "local",
                            "nodes": node_count,
                            "kinds": kinds
                        }
                        category_labs["labs"].append(lab_info)
                    except Exception as e:
                        logger.error(f"Error loading lab file {lab_file}: {e}")
                        continue
                
                # Only add category if it has labs
                if category_labs["labs"]:
                    labs.append(category_labs)
    
    # GitHub labs
    if include_github:
        github_labs = lab_scanner.load_labs()
        if github_labs and "repositories" in github_labs:
            for repo, repo_labs in github_labs["repositories"].items():
                if repo_labs:
                    github_category = {
                        "category": f"github-{repo.replace('/', '-')}",
                        "source": "github",
                        "repository": repo,
                        "labs": repo_labs
                    }
                    labs.append(github_category)
    
    return labs

@app.post("/api/labs/scan")
async def scan_github_labs():
    """Scan GitHub repositories for lab definitions"""
    labs = await lab_scanner.refresh_labs()
    return {"message": "GitHub lab scan completed", "results": labs}

@app.get("/api/containers")
async def get_containers(refresh: bool = False):
    """Get all available containers"""
    if refresh:
        containers = await container_service.discover_all_containers()
    else:
        containers = container_service.load_containers()
        if not containers:
            # First time - discover containers
            containers = await container_service.discover_all_containers()
    
    return containers

@app.post("/api/containers/refresh")
async def refresh_containers():
    """Refresh container discovery from all sources"""
    containers = await container_service.refresh_containers()
    return {"message": "Container discovery completed", "containers": containers}

@app.post("/api/labs/launch")
async def launch_lab(request: dict):
    """Launch a containerlab topology from a file path"""
    lab_file_path = request.get("lab_file_path")
    if not lab_file_path:
        raise HTTPException(status_code=400, detail={"message": "lab_file_path is required"})
    
    result = await lab_launcher.launch_lab(lab_file_path)
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.post("/api/labs/{lab_id}/stop")
async def stop_lab(lab_id: str):
    """Stop a running lab"""
    result = await lab_launcher.stop_lab(lab_id)
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.get("/api/labs/{lab_id}/status")
async def get_lab_status(lab_id: str):
    """Get the status of a specific lab"""
    result = await lab_launcher.get_lab_status(lab_id)
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=404, detail=result)

@app.get("/api/labs/active")
async def list_active_labs():
    """List all active/running labs"""
    labs = await lab_launcher.list_active_labs()
    return {"active_labs": labs, "count": len(labs)}

@app.post("/api/labs/create")
async def create_lab(lab_config: dict):
    """Create a new custom lab"""
    # This will generate containerlab topology files
    return {"message": "Lab creation will be implemented", "config": lab_config}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "LabDabbler API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
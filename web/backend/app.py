from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml
import json
from pathlib import Path
from services.container_discovery import ContainerDiscoveryService
from services.github_lab_scanner import GitHubLabScanner

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

# Initialize services
container_service = ContainerDiscoveryService(DATA_DIR)
lab_scanner = GitHubLabScanner(DATA_DIR)

@app.get("/")
async def root():
    return {"message": "LabDabbler Master Lab Repository API", "version": "1.0.0"}

@app.get("/api/labs")
async def get_labs(include_github: bool = True):
    """Get all available labs"""
    labs = []
    
    # Local labs from filesystem
    if LABS_DIR.exists():
        for category in LABS_DIR.iterdir():
            if category.is_dir():
                category_labs = {
                    "category": category.name,
                    "source": "local",
                    "labs": []
                }
                for lab in category.iterdir():
                    if lab.is_dir():
                        lab_info = {
                            "name": lab.name,
                            "path": str(lab.relative_to(Path.cwd())),
                            "description": f"{category.name.title()} lab: {lab.name}",
                            "source": "local"
                        }
                        category_labs["labs"].append(lab_info)
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
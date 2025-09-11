from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import yaml
import json
import logging
from pathlib import Path
from services.container_discovery import ContainerDiscoveryService
from services.github_lab_scanner import GitHubLabScanner
from services.lab_launcher import LabLauncherService
from services.vrnetlab_service import VRNetLabService
from services.repository_management import RepositoryManagementService

logger = logging.getLogger(__name__)

# Initialize services at module level
container_service = ContainerDiscoveryService(Path("./data"))
lab_scanner = GitHubLabScanner(Path("./data"))
lab_launcher = LabLauncherService(Path("./data"))
vrnetlab_service = VRNetLabService(Path("./data"))
repository_service = RepositoryManagementService(Path("./data"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting LabDabbler backend services...")
    try:
        await repository_service.start_background_sync()
        logger.info("Background sync scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start background sync scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LabDabbler backend services...")
    try:
        await repository_service.stop_background_sync()
        logger.info("Background sync scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping background sync scheduler: {e}")

app = FastAPI(title="LabDabbler - Master Lab Repository", version="1.0.0", lifespan=lifespan)

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

# Update service data directories to use PROJECT_ROOT/data
container_service.data_dir = DATA_DIR
lab_scanner.data_dir = DATA_DIR
lab_launcher.data_dir = DATA_DIR
vrnetlab_service.data_dir = DATA_DIR
repository_service.data_dir = DATA_DIR

@app.get("/")
async def root():
    return {"message": "LabDabbler Master Lab Repository API", "version": "1.0.0"}

@app.get("/api/labs")
async def get_labs(include_github: bool = True, include_repositories: bool = True):
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
    
    # Repository labs (new centralized repository management)
    if include_repositories:
        try:
            repository_labs = await repository_service.get_all_labs_from_repositories()
            
            # Group repository labs by repository
            repo_lab_groups = {}
            for lab in repository_labs:
                repo_name = lab.get("repository", "unknown")
                if repo_name not in repo_lab_groups:
                    repo_lab_groups[repo_name] = {
                        "category": f"repo-{repo_name}",
                        "source": "repository",
                        "repository": repo_name,
                        "labs": []
                    }
                repo_lab_groups[repo_name]["labs"].append(lab)
            
            # Add repository lab groups to the main labs list
            for repo_group in repo_lab_groups.values():
                if repo_group["labs"]:
                    labs.append(repo_group)
                    
        except Exception as e:
            logger.error(f"Error loading repository labs: {e}")
    
    # GitHub labs (legacy support)
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

@app.get("/api/containers/search")
async def search_containers(
    q: str = "",
    category: str = "", 
    vendor: str = "",
    architecture: str = "",
    limit: int = 50,
    offset: int = 0
):
    """Search containers with filters and pagination"""
    results = container_service.search_containers(
        query=q, 
        category=category, 
        vendor=vendor, 
        architecture=architecture
    )
    
    # Apply pagination
    total = results["total"]
    paginated_results = results["results"][offset:offset + limit]
    
    return {
        "total": total,
        "results": paginated_results,
        "categories": results["categories"],
        "query": results["query"],
        "filters": results["filters"],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    }

@app.get("/api/containers/categories")
async def get_container_categories():
    """Get all container categories with metadata and counts"""
    categories = container_service.get_container_categories()
    return {"categories": categories}

@app.get("/api/containers/vendors")
async def get_container_vendors():
    """Get list of all container vendors"""
    vendors = container_service.get_vendors()
    return {"vendors": vendors}

@app.get("/api/containers/architectures")
async def get_container_architectures():
    """Get list of all supported architectures"""
    architectures = container_service.get_architectures()
    return {"architectures": architectures}

@app.get("/api/containers/stats")
async def get_container_stats():
    """Get statistics about the container catalog"""
    containers = container_service.load_containers()
    if not containers:
        return {"total_containers": 0, "total_categories": 0, "vendors": [], "last_updated": None}
    
    total_containers = 0
    categories = []
    
    for category_name, container_list in containers.items():
        if category_name == "last_updated":
            continue
        if isinstance(container_list, list):
            total_containers += len(container_list)
            categories.append(category_name)
    
    return {
        "total_containers": total_containers,
        "total_categories": len(categories),
        "categories": categories,
        "vendors": container_service.get_vendors(),
        "architectures": container_service.get_architectures(),
        "last_updated": containers.get("last_updated")
    }

@app.post("/api/containers/refresh")
async def refresh_containers():
    """Refresh container discovery from all sources"""
    containers = await container_service.refresh_containers()
    stats = {
        "total_containers": sum(len(v) if isinstance(v, list) else 0 for v in containers.values()),
        "total_categories": len([k for k in containers.keys() if k != "last_updated"]),
        "last_updated": containers.get("last_updated")
    }
    return {"message": "Container discovery completed", "stats": stats}

@app.post("/api/containers/validate-compatibility")
async def validate_container_compatibility(
    request: dict
):
    """Validate container compatibility with a specific lab type"""
    container_data = request.get("container")
    lab_type = request.get("lab_type")
    protocols = request.get("protocols", [])
    
    if not container_data or not lab_type:
        raise HTTPException(status_code=400, detail="container and lab_type are required")
    
    compatibility = await container_service.validate_container_compatibility(
        container_data, lab_type, protocols
    )
    return compatibility

@app.get("/api/containers/recommendations/{lab_type}")
async def get_recommended_containers(
    lab_type: str,
    lab_description: str = None,
    protocols: str = None,  # Comma-separated list
    limit: int = 10
):
    """Get recommended containers for a specific lab type"""
    protocol_list = protocols.split(",") if protocols else None
    recommendations = await container_service.get_recommended_containers_for_lab(
        lab_type, lab_description, protocol_list, limit
    )
    return recommendations

@app.post("/api/labs/{lab_id}/analyze-requirements")
async def analyze_lab_container_requirements(lab_id: str):
    """Analyze a lab configuration and suggest required containers"""
    # First try to load the lab from GitHub data
    github_labs = lab_scanner.load_labs()
    lab_config = None
    
    if github_labs and "repositories" in github_labs:
        for repo, repo_labs in github_labs["repositories"].items():
            for lab in repo_labs:
                if lab.get("name") == lab_id or lab.get("file_path", "").endswith(f"/{lab_id}.clab.yml"):
                    # Load the actual lab config if we have the URL
                    if "raw_url" in lab:
                        try:
                            import requests
                            response = requests.get(lab["raw_url"])
                            if response.status_code == 200:
                                lab_config = yaml.safe_load(response.text)
                                break
                        except Exception as e:
                            logger.error(f"Error loading lab config from {lab.get('raw_url')}: {e}")
    
    # If not found in GitHub, try local labs
    if not lab_config and LABS_DIR.exists():
        for lab_file in LABS_DIR.rglob(f"*{lab_id}*.clab.yml"):
            try:
                with open(lab_file, 'r') as f:
                    lab_config = yaml.safe_load(f)
                break
            except Exception as e:
                logger.error(f"Error loading local lab file {lab_file}: {e}")
    
    if not lab_config:
        raise HTTPException(status_code=404, detail=f"Lab configuration not found for ID: {lab_id}")
    
    suggestions = await container_service.analyze_lab_container_requirements(lab_config)
    return suggestions

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

# VRNetlab endpoints
@app.post("/api/vrnetlab/init")
async def initialize_vrnetlab_repo():
    """Initialize or update the vrnetlab repository"""
    result = await vrnetlab_service.initialize_vrnetlab_repo()
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.post("/api/vrnetlab/upload")
async def upload_vm_image(
    file: UploadFile = File(...),
    vendor: str = Form(...),
    platform: str = Form(...),
    version: str = Form("latest")
):
    """Upload a VM image for vrnetlab conversion"""
    try:
        # Read file content
        file_data = await file.read()
        
        # Validate file has a filename
        if not file.filename:
            raise HTTPException(status_code=400, detail={"message": "File must have a filename"})
        
        # Upload the image
        result = await vrnetlab_service.upload_vm_image(
            file_data, file.filename, vendor, platform, version
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e), "message": "Failed to upload VM image"})

@app.post("/api/vrnetlab/build")
async def build_vrnetlab_container(request: dict):
    """Build a vrnetlab container from uploaded VM image"""
    image_id = request.get("image_id")
    container_name = request.get("container_name")
    container_tag = request.get("container_tag", "latest")
    
    if not image_id:
        raise HTTPException(status_code=400, detail={"message": "image_id is required"})
    
    # Container name is optional - will be auto-generated if not provided
    result = await vrnetlab_service.build_vrnetlab_container(image_id, container_name, container_tag)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.get("/api/vrnetlab/builds/{build_id}/status")
async def get_build_status(build_id: str):
    """Get the status of a vrnetlab build"""
    result = await vrnetlab_service.get_build_status(build_id)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=404, detail=result)

@app.get("/api/vrnetlab/images")
async def list_vm_images():
    """List all uploaded VM images"""
    result = await vrnetlab_service.list_vm_images()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.get("/api/vrnetlab/builds")
async def list_builds():
    """List all vrnetlab builds"""
    result = await vrnetlab_service.list_builds()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.get("/api/vrnetlab/containers")
async def list_built_containers():
    """List all built vrnetlab containers"""
    result = await vrnetlab_service.list_built_containers()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.delete("/api/vrnetlab/images/{image_id}")
async def delete_vm_image(image_id: str):
    """Delete a VM image"""
    result = await vrnetlab_service.delete_vm_image(image_id)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.get("/api/vrnetlab/vendors")
async def get_supported_vendors():
    """Get list of supported vendors and platforms"""
    return {
        "success": True,
        "vendors": vrnetlab_service.supported_vendors
    }

# Repository Management API Endpoints

@app.post("/api/repositories/initialize")
async def initialize_repositories():
    """Initialize the repository management system with default repositories"""
    result = await repository_service.initialize_repositories()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.get("/api/repositories")
async def get_repositories():
    """Get all managed repositories"""
    result = await repository_service.get_all_repositories()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result)

@app.get("/api/repositories/{repo_name}/status")
async def get_repository_status(repo_name: str):
    """Get detailed status of a specific repository"""
    result = await repository_service.get_repository_status(repo_name)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=404, detail=result)

@app.post("/api/repositories/{repo_name}/sync")
async def sync_repository(repo_name: str):
    """Sync a specific repository"""
    result = await repository_service.sync_repository(repo_name)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.post("/api/repositories/sync-all")
async def sync_all_repositories():
    """Sync all configured repositories"""
    result = await repository_service.sync_all_repositories()
    return result

@app.post("/api/repositories/add")
async def add_repository(request: dict):
    """Add a new repository to the configuration"""
    result = await repository_service.add_repository(request)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.delete("/api/repositories/{repo_name}")
async def remove_repository(repo_name: str):
    """Remove a repository from the configuration"""
    result = await repository_service.remove_repository(repo_name)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result)

@app.get("/api/repositories/labs")
async def get_repository_labs():
    """Get all labs from managed repositories"""
    labs = await repository_service.get_all_labs_from_repositories()
    return {
        "success": True,
        "labs": labs,
        "total_labs": len(labs)
    }

@app.post("/api/repositories/auto-sync")
async def auto_sync_repositories():
    """Perform automatic sync for repositories with auto_sync enabled"""
    result = await repository_service.auto_sync_repositories()
    return result

@app.get("/api/repositories/sync-status")
async def get_sync_status():
    """Get sync status for all repositories"""
    status = await repository_service.get_sync_status()
    return {
        "success": True,
        "sync_status": status
    }

@app.get("/api/repositories/scheduler-status")
async def get_scheduler_status():
    """Get status of the background sync scheduler"""
    status = repository_service.get_scheduler_status()
    return {
        "success": True,
        "scheduler_status": status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
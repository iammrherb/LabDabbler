from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml
import json
from pathlib import Path

app = FastAPI(title="LabDabbler - Master Lab Repository", version="1.0.0")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage
LABS_DIR = Path("./labs")
CONFIGS_DIR = Path("./configs")
DATA_DIR = Path("./data")

@app.get("/")
async def root():
    return {"message": "LabDabbler Master Lab Repository API", "version": "1.0.0"}

@app.get("/api/labs")
async def get_labs():
    """Get all available labs"""
    labs = []
    if LABS_DIR.exists():
        for category in LABS_DIR.iterdir():
            if category.is_dir():
                category_labs = {
                    "category": category.name,
                    "labs": []
                }
                for lab in category.iterdir():
                    if lab.is_dir():
                        lab_info = {
                            "name": lab.name,
                            "path": str(lab.relative_to(Path.cwd())),
                            "description": f"{category.name.title()} lab: {lab.name}"
                        }
                        category_labs["labs"].append(lab_info)
                labs.append(category_labs)
    return labs

@app.get("/api/containers")
async def get_containers():
    """Get all available containers"""
    # This will be populated with Docker Hub scanning
    containers = {
        "portnox": [
            {"name": "local-radius", "image": "portnox/local-radius:latest", "description": "Portnox Local RADIUS Server"},
            {"name": "tacacs", "image": "portnox/tacacs:latest", "description": "Portnox TACACS+ Server"},
            {"name": "dhcp", "image": "portnox/dhcp:latest", "description": "Portnox DHCP Server"},
            {"name": "ztna-gateway", "image": "portnox/ztna-gateway:latest", "description": "Portnox ZTNA Gateway"}
        ],
        "network_os": [
            {"name": "nokia-srlinux", "image": "ghcr.io/nokia/srlinux:latest", "kind": "nokia_srlinux"},
            {"name": "arista-ceos", "image": "ceos:latest", "kind": "arista_ceos"},
            {"name": "frr", "image": "frrouting/frr:latest", "kind": "linux"}
        ],
        "security": [
            {"name": "kali", "image": "kalilinux/kali-rolling:latest", "description": "Kali Linux"},
            {"name": "metasploit", "image": "metasploitframework/metasploit-framework:latest", "description": "Metasploit"}
        ]
    }
    return containers

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
"""
Production-ready FastAPI application for LabDabbler backend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import os
import yaml
import json
import logging
import asyncio
import redis
from pathlib import Path

# Import existing services
from services.container_discovery import ContainerDiscoveryService
from services.github_lab_scanner import GitHubLabScanner
from services.lab_launcher import LabLauncherService
from services.vrnetlab_service import VRNetLabService
from services.repository_management import RepositoryManagementService

# Import production middleware and utilities
from middleware.security import SecurityMiddleware, RateLimiter, InputValidationMiddleware
from middleware.performance import CacheMiddleware, CompressionMiddleware, MetricsMiddleware
from utils.secrets import get_secret, env_secrets
from config.settings import settings

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/labdabbler/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Redis for caching and rate limiting
redis_client = None
try:
    redis_url = env_secrets.get_redis_url()
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()  # Test connection
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Caching and rate limiting disabled.")

# Initialize services
container_service = ContainerDiscoveryService(Path("./data"))
lab_scanner = GitHubLabScanner(Path("./data"))
lab_launcher = LabLauncherService(Path("./data"))
vrnetlab_service = VRNetLabService(Path("./data"))
repository_service = RepositoryManagementService(Path("./data"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting LabDabbler production backend...")
    try:
        await repository_service.start_background_sync()
        logger.info("Background sync scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start background sync scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LabDabbler production backend...")
    try:
        await repository_service.stop_background_sync()
        if redis_client:
            redis_client.close()
        logger.info("Backend shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with production configuration
app = FastAPI(
    title="LabDabbler - Master Lab Repository",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add security middleware
if redis_client:
    rate_limiter = RateLimiter(redis_client)
    app.add_middleware(SecurityMiddleware, rate_limiter=rate_limiter)
else:
    app.add_middleware(SecurityMiddleware)

app.add_middleware(InputValidationMiddleware)

# Add performance middleware
if redis_client:
    app.add_middleware(CacheMiddleware, redis_client=redis_client)
    app.add_middleware(MetricsMiddleware, redis_client=redis_client)

app.add_middleware(CompressionMiddleware)

# Add trusted host middleware for production
trusted_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Configure CORS with production settings
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Response-Time"],
)

# Data storage paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = PROJECT_ROOT / "labs"
CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"

# Update service data directories
container_service.data_dir = DATA_DIR
lab_scanner.data_dir = DATA_DIR
lab_launcher.data_dir = DATA_DIR
vrnetlab_service.data_dir = DATA_DIR
repository_service.data_dir = DATA_DIR

# Import all existing routes from original app.py
# (The routes remain the same, just importing the original file content)
from app import *  # Import all routes from the original app

# Add production-specific endpoints
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint in text exposition format"""
    if not redis_client:
        # Return basic metrics even without Redis
        metrics_text = """# HELP labdabbler_up Application up status
# TYPE labdabbler_up gauge
labdabbler_up 1

# HELP labdabbler_redis_available Redis availability status
# TYPE labdabbler_redis_available gauge
labdabbler_redis_available 0
"""
        return Response(content=metrics_text, media_type="text/plain")
    
    try:
        # Build Prometheus format metrics
        metrics_lines = []
        
        # Application up metric
        metrics_lines.extend([
            "# HELP labdabbler_up Application up status",
            "# TYPE labdabbler_up gauge",
            "labdabbler_up 1",
            ""
        ])
        
        # Redis availability
        metrics_lines.extend([
            "# HELP labdabbler_redis_available Redis availability status", 
            "# TYPE labdabbler_redis_available gauge",
            "labdabbler_redis_available 1",
            ""
        ])
        
        # Request counters
        metrics_lines.extend([
            "# HELP labdabbler_requests_total Total number of requests",
            "# TYPE labdabbler_requests_total counter"
        ])
        
        request_keys = redis_client.keys("metrics:requests:*")
        for key in request_keys:
            count = redis_client.get(key) or "0"
            endpoint = key.replace("metrics:requests:", "")
            metrics_lines.append(f'labdabbler_requests_total{{endpoint="{endpoint}"}} {count}')
        
        if not request_keys:
            metrics_lines.append('labdabbler_requests_total{endpoint="unknown"} 0')
        metrics_lines.append("")
        
        # Response times
        metrics_lines.extend([
            "# HELP labdabbler_response_time_seconds Average response time in seconds",
            "# TYPE labdabbler_response_time_seconds gauge"
        ])
        
        timing_keys = redis_client.keys("metrics:timing:*")
        for key in timing_keys:
            timings = redis_client.lrange(key, 0, -1)
            if timings:
                avg_time = sum(float(t) for t in timings) / len(timings)
                endpoint = key.replace("metrics:timing:", "")
                metrics_lines.append(f'labdabbler_response_time_seconds{{endpoint="{endpoint}"}} {avg_time:.6f}')
        
        if not timing_keys:
            metrics_lines.append('labdabbler_response_time_seconds{endpoint="unknown"} 0')
        metrics_lines.append("")
        
        # Slow requests counter
        slow_requests = redis_client.lrange("metrics:slow_requests", 0, -1)
        metrics_lines.extend([
            "# HELP labdabbler_slow_requests_total Total number of slow requests",
            "# TYPE labdabbler_slow_requests_total counter",
            f"labdabbler_slow_requests_total {len(slow_requests)}",
            ""
        ])
        
        metrics_text = "\n".join(metrics_lines)
        return Response(content=metrics_text, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        # Return error metric in Prometheus format
        error_metrics = """# HELP labdabbler_up Application up status
# TYPE labdabbler_up gauge
labdabbler_up 1

# HELP labdabbler_metrics_error Metrics collection error status
# TYPE labdabbler_metrics_error gauge
labdabbler_metrics_error 1
"""
        return Response(content=error_metrics, media_type="text/plain")

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check for monitoring"""
    health = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            health["services"]["redis"] = {"status": "healthy"}
        else:
            health["services"]["redis"] = {"status": "disabled"}
    except Exception as e:
        health["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    # Check database (if configured)
    # This would integrate with your database connection
    health["services"]["database"] = {"status": "not_implemented"}
    
    # Check file system
    try:
        DATA_DIR.exists()
        health["services"]["filesystem"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["filesystem"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    return health

if __name__ == "__main__":
    import uvicorn
    
    # Production server configuration
    uvicorn.run(
        "app_production:app",
        host="0.0.0.0",
        port=8000,
        workers=int(os.getenv("WORKER_PROCESSES", "4")),
        log_level="info",
        access_log=True,
        server_header=False,
        date_header=False
    )
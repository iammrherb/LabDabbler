"""
Performance middleware for LabDabbler production backend
"""
import gzip
import time
import json
from typing import Any, Dict, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp
import redis
import logging

logger = logging.getLogger(__name__)

class CacheMiddleware(BaseHTTPMiddleware):
    """Redis-based caching middleware"""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis, default_ttl: int = 300):
        super().__init__(app)
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cacheable_methods = {"GET", "HEAD"}
        self.cacheable_paths = {
            "/api/containers": 3600,  # Cache for 1 hour
            "/api/labs": 300,  # Cache for 5 minutes
            "/api/repositories": 1800,  # Cache for 30 minutes
            "/api/containers/categories": 3600,
            "/api/containers/vendors": 3600,
            "/api/containers/architectures": 3600,
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check if request is cacheable
        if not self._is_cacheable(request):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        try:
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.url.path}")
                return cached_response
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            try:
                await self._save_to_cache(cache_key, response, request.url.path)
            except Exception as e:
                logger.warning(f"Cache save error: {e}")
        
        return response
    
    def _is_cacheable(self, request: Request) -> bool:
        """Check if request can be cached"""
        if request.method not in self.cacheable_methods:
            return False
        
        path = request.url.path
        return any(path.startswith(cacheable_path) for cacheable_path in self.cacheable_paths)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        path = request.url.path
        query = str(request.url.query)
        return f"cache:{path}:{hash(query)}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Response]:
        """Get response from cache"""
        cached_data = self.redis.get(cache_key)
        if not cached_data:
            return None
        
        try:
            data = json.loads(cached_data)
            return Response(
                content=data["content"],
                status_code=data["status_code"],
                headers=data["headers"],
                media_type=data.get("media_type", "application/json")
            )
        except (json.JSONDecodeError, KeyError):
            # Invalid cache data, delete it
            self.redis.delete(cache_key)
            return None
    
    async def _save_to_cache(self, cache_key: str, response: Response, path: str):
        """Save response to cache"""
        # Get TTL for this path
        ttl = self.default_ttl
        for cacheable_path, path_ttl in self.cacheable_paths.items():
            if path.startswith(cacheable_path):
                ttl = path_ttl
                break
        
        # Only cache if response has body attribute (meaning it's a standard Response)
        if hasattr(response, 'body'):
            body = response.body
            
            # Prepare cache data
            cache_data = {
                "content": body.decode("utf-8") if isinstance(body, bytes) else str(body),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": getattr(response, 'media_type', 'application/json')
            }
            
            # Save to cache
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )

class CompressionMiddleware(BaseHTTPMiddleware):
    """Response compression middleware"""
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024, compression_level: int = 6):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.compressible_types = {
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "text/plain",
            "application/xml",
            "text/xml"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check if client accepts gzip encoding
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return await call_next(request)
        
        response = await call_next(request)
        
        # Check if response should be compressed
        if not self._should_compress(response):
            return response
        
        # Compress response
        return await self._compress_response(response)
    
    def _should_compress(self, response: Response) -> bool:
        """Check if response should be compressed"""
        # Don't compress if already compressed
        if response.headers.get("content-encoding"):
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in self.compressible_types):
            return False
        
        # Check content length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.minimum_size:
            return False
        
        return True
    
    async def _compress_response(self, response: Response) -> Response:
        """Compress response body"""
        # Only compress if response has body attribute
        if not hasattr(response, 'body'):
            return response
            
        body = response.body
        if isinstance(body, str):
            body = body.encode('utf-8')
        
        # Check minimum size
        if len(body) < self.minimum_size:
            return response
        
        # Compress body
        compressed_body = gzip.compress(body, compresslevel=self.compression_level)
        
        # Create new response with compressed body
        new_response = Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=getattr(response, 'media_type', None)
        )
        
        # Update headers
        new_response.headers["content-encoding"] = "gzip"
        new_response.headers["content-length"] = str(len(compressed_body))
        new_response.headers["vary"] = "Accept-Encoding"
        
        return new_response

class MetricsMiddleware(BaseHTTPMiddleware):
    """Performance metrics collection middleware"""
    
    def __init__(self, app: ASGIApp, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        
        # Collect metrics
        await self._collect_metrics(request, response, duration)
        
        # Add performance headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
    
    async def _collect_metrics(self, request: Request, response: Response, duration: float):
        """Collect performance metrics"""
        try:
            path = request.url.path
            method = request.method
            status = response.status_code
            
            # Increment request counter
            counter_key = f"metrics:requests:{method}:{path}:{status}"
            self.redis.incr(counter_key)
            self.redis.expire(counter_key, 3600)  # Expire after 1 hour
            
            # Track response times
            timing_key = f"metrics:timing:{method}:{path}"
            self.redis.lpush(timing_key, duration)
            self.redis.ltrim(timing_key, 0, 99)  # Keep last 100 measurements
            self.redis.expire(timing_key, 3600)
            
            # Track slow requests (>1 second)
            if duration > 1.0:
                slow_key = f"metrics:slow_requests"
                self.redis.lpush(slow_key, f"{method} {path} - {duration:.3f}s")
                self.redis.ltrim(slow_key, 0, 49)  # Keep last 50 slow requests
                self.redis.expire(slow_key, 3600)
                
        except Exception as e:
            logger.warning(f"Metrics collection error: {e}")
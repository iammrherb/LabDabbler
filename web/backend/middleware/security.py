"""
Security middleware for LabDabbler production backend
"""
import time
import hashlib
import ipaddress
from collections import defaultdict
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation using Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        try:
            current_time = int(time.time())
            pipe = self.redis.pipeline()
            
            # Clean old entries
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < limit
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if Redis is down
            return True

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.blocked_ips = set()
        self.suspicious_patterns = [
            "../../",  # Path traversal
            "<script",  # XSS attempts
            "union select",  # SQL injection
            "drop table",  # SQL injection
            "exec(",  # Code injection
            "__import__",  # Python injection
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Security checks
        try:
            await self._security_checks(request, client_ip)
        except HTTPException as e:
            return Response(
                content=f"Security violation: {e.detail}",
                status_code=e.status_code,
                headers={"Content-Type": "text/plain"}
            )
        
        # Rate limiting
        if self.rate_limiter:
            try:
                await self._rate_limit_check(request, client_ip)
            except HTTPException as e:
                return Response(
                    content="Rate limit exceeded",
                    status_code=e.status_code,
                    headers={"Content-Type": "text/plain"}
                )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        # Log request
        process_time = time.time() - start_time
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} - {response.status_code} "
            f"({process_time:.3f}s)"
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header (from proxy)
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    async def _security_checks(self, request: Request, client_ip: str):
        """Perform various security checks"""
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address blocked"
            )
        
        # Check for suspicious patterns in URL and headers
        url_path = str(request.url.path).lower()
        query_string = str(request.url.query).lower()
        
        for pattern in self.suspicious_patterns:
            if pattern in url_path or pattern in query_string:
                logger.warning(
                    f"Suspicious pattern '{pattern}' detected from {client_ip}: "
                    f"{request.method} {request.url}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malicious request detected"
                )
        
        # Check User-Agent header
        user_agent = request.headers.get("User-Agent", "").lower()
        suspicious_agents = ["sqlmap", "nikto", "masscan", "nmap"]
        if any(agent in user_agent for agent in suspicious_agents):
            logger.warning(f"Suspicious User-Agent from {client_ip}: {user_agent}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Blocked User-Agent"
            )
        
        # Validate Content-Length
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                length = int(content_length)
                # Block extremely large requests (>2GB)
                if length > 2 * 1024 * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header"
                )
    
    async def _rate_limit_check(self, request: Request, client_ip: str):
        """Check rate limits for the request"""
        path = request.url.path
        method = request.method
        
        # Define rate limits for different endpoints
        rate_limits = {
            "/api/auth/login": (5, 300),  # 5 requests per 5 minutes
            "/api/labs/launch": (10, 3600),  # 10 requests per hour
            "/api/vrnetlab/upload": (3, 3600),  # 3 uploads per hour
            "/api/containers/refresh": (2, 3600),  # 2 refreshes per hour
        }
        
        # Default rate limit for all other API endpoints
        default_limit = (100, 3600)  # 100 requests per hour
        
        # Get rate limit for this endpoint
        limit, window = rate_limits.get(path, default_limit)
        
        # Create rate limit key
        rate_key = f"rate_limit:{client_ip}:{path}:{method}"
        
        # Check rate limit (if rate limiter is available)
        if self.rate_limiter and not self.rate_limiter.is_allowed(rate_key, limit, window):
            logger.warning(
                f"Rate limit exceeded for {client_ip}: "
                f"{method} {path} ({limit}/{window}s)"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "no-referrer-when-downgrade",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            ),
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            "Server": "LabDabbler/1.0"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB
            return Response(
                content="Request body too large",
                status_code=413,
                headers={"Content-Type": "text/plain"}
            )
        
        # Validate JSON content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not content_type.startswith(("application/json", "multipart/form-data")):
                if not request.url.path.startswith("/docs"):  # Allow Swagger docs
                    return Response(
                        content="Invalid content type",
                        status_code=415,
                        headers={"Content-Type": "text/plain"}
                    )
        
        response = await call_next(request)
        return response

# JWT Bearer token security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return current user"""
    # This would integrate with your authentication system
    # For now, it's a placeholder
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement JWT validation
    return {"user_id": "placeholder", "username": "placeholder"}
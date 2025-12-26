"""
HTTP Proxy Server for LLM PII Protection.

A transparent HTTP proxy that sits between your application and LLM providers
(OpenAI, Anthropic, etc.), automatically anonymizing PII in requests and
de-anonymizing responses.

Features:
- Zero code changes required - just point your API endpoint to the proxy
- Supports OpenAI, Anthropic, and generic LLM APIs
- Automatic PII detection and anonymization
- Request/response logging with anonymized data
- Health monitoring and metrics
- Rate limiting
- Redis-based session management

Usage:
    python main.py --port 8000 --redis-url redis://localhost:6379
"""

import sys
import os
import asyncio
import json
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

# Add parent package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../python/src"))

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
import redis

from prompt_guard import PromptGuard, configure_logging, get_logger
from prompt_guard.storage.redis_storage import RedisMappingStorage
from rate_limiter import (
    TokenBucketRateLimiter,
    GlobalRateLimiter,
    RateLimitConfig,
    RateLimitExceeded,
)

# Configure structured JSON logging
configure_logging(level="INFO", json_format=True)
logger = get_logger("proxy")


@dataclass
class ProxyConfig:
    """Configuration for the proxy server."""
    port: int = 8000
    host: str = "0.0.0.0"
    redis_url: str = "redis://localhost:6379"
    policy: str = "default_pii"
    detectors: List[str] = None
    enable_metrics: bool = True
    enable_audit: bool = True
    # Rate limiting configuration
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    global_requests_per_second: int = 100
    burst_size: int = 10
    trusted_ips: List[str] = None


class LLMProxy:
    """
    HTTP proxy for LLM API calls with PII protection.

    Supported providers:
    - OpenAI (api.openai.com)
    - Anthropic (api.anthropic.com)
    - Generic (configurable)
    """

    # Provider configurations
    PROVIDERS = {
        "openai": {
            "base_url": "https://api.openai.com",
            "auth_header": "Authorization",
            "message_paths": ["messages", "prompt"],
        },
        "anthropic": {
            "base_url": "https://api.anthropic.com",
            "auth_header": "x-api-key",
            "message_paths": ["messages", "prompt"],
        },
    }

    def __init__(self, config: ProxyConfig):
        """
        Initialize the LLM proxy.

        Args:
            config: Proxy configuration
        """
        self.config = config
        self.guard = PromptGuard(
            detectors=config.detectors or ["regex"],
            policy=config.policy,
        )
        self.storage = RedisMappingStorage(
            redis_url=config.redis_url,
            enable_audit=config.enable_audit,
        )
        
        # Initialize rate limiters
        self.rate_limiter = None
        self.global_limiter = None
        if config.enable_rate_limiting:
            redis_client = redis.from_url(config.redis_url, decode_responses=True)
            rate_limit_config = RateLimitConfig(
                requests_per_minute=config.requests_per_minute,
                requests_per_hour=config.requests_per_hour,
                burst_size=config.burst_size,
                trusted_ips=set(config.trusted_ips or []),
            )
            self.rate_limiter = TokenBucketRateLimiter(redis_client, rate_limit_config)
            self.global_limiter = GlobalRateLimiter(
                redis_client, config.global_requests_per_second
            )
        
        self.metrics = {
            "requests_total": 0,
            "requests_anonymized": 0,
            "pii_detected": 0,
            "errors": 0,
            "rate_limit_exceeded": 0,
        }

    async def proxy_request(
        self,
        provider: str,
        endpoint: str,
        request: Request,
    ) -> JSONResponse | StreamingResponse:
        """
        Proxy an LLM API request with PII protection.

        Args:
            provider: Provider name (e.g., "openai")
            endpoint: API endpoint path
            request: Incoming request

        Returns:
            Proxied response (with de-anonymized content)
        """
        self.metrics["requests_total"] += 1

        # Get client context
        client_ip = request.client.host if request.client else "unknown"
        user_id = request.headers.get("X-User-ID")
        
        # Set logging context
        request_id = logger.set_request_id()
        if user_id:
            logger.set_user_id(user_id)
        
        # Check rate limits
        if self.rate_limiter:
            try:
                # Check global rate limit first
                if self.global_limiter:
                    self.global_limiter.check_global_limit()
                
                # Check per-user/IP rate limit
                self.rate_limiter.check_rate_limit(client_ip, user_id)
                
            except RateLimitExceeded as e:
                self.metrics["rate_limit_exceeded"] += 1
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    limit_type=e.limit_type,
                    retry_after=e.retry_after,
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Retry after {e.retry_after} seconds.",
                    headers={"Retry-After": str(e.retry_after)},
                )

        # Get provider config
        provider_config = self.PROVIDERS.get(provider)
        if not provider_config:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        try:
            # Get request body
            body = await request.json()

            # Create session
            session_id = self.storage.create_session(
                user_id=user_id,
                metadata={"provider": provider, "endpoint": endpoint},
            )
            logger.set_session_id(session_id)

            # Anonymize messages in the request
            anonymized_body, mapping = self._anonymize_request_body(body, provider_config)

            # Store mapping for this session
            if mapping:
                self.storage.store_mapping(session_id, mapping)
                self.metrics["requests_anonymized"] += 1
                self.metrics["pii_detected"] += len(mapping)
                
                # Log PII detection (without values)
                entity_types = list(set([k.split('_')[0].strip('[]') for k in mapping.keys()]))
                logger.info(
                    "PII detected and anonymized",
                    entity_count=len(mapping),
                    entity_types=entity_types,
                    provider=provider,
                )

            # Build target URL
            target_url = f"{provider_config['base_url']}{endpoint}"

            # Forward headers (excluding host)
            headers = dict(request.headers)
            headers.pop("host", None)
            headers["X-Session-ID"] = session_id  # Add session ID for tracking

            # Make the proxied request
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    json=anonymized_body,
                    headers=headers,
                    timeout=60.0,
                )

            # Handle streaming responses
            if "stream" in body and body.get("stream"):
                return await self._handle_streaming_response(
                    response, mapping, session_id
                )

            # Handle regular responses
            response_data = response.json()

            # De-anonymize response
            if mapping:
                response_data = self._deanonymize_response_body(
                    response_data, mapping, provider_config
                )

            return JSONResponse(
                content=response_data,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(
                "Proxy request failed",
                exc_info=True,
                provider=provider,
                endpoint=endpoint,
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Clear logging context
            logger.clear_context()

    def _anonymize_request_body(
        self,
        body: Dict,
        provider_config: Dict,
    ) -> tuple[Dict, Dict[str, str]]:
        """
        Anonymize PII in request body.

        Args:
            body: Request body
            provider_config: Provider configuration

        Returns:
            Tuple of (anonymized_body, pii_mapping)
        """
        anonymized_body = body.copy()
        combined_mapping = {}

        # Find and anonymize message fields
        message_paths = provider_config["message_paths"]

        for path in message_paths:
            if path in anonymized_body:
                content = anonymized_body[path]

                # Handle different message formats
                if isinstance(content, str):
                    anonymized, mapping = self.guard.anonymize(content)
                    anonymized_body[path] = anonymized
                    combined_mapping.update(mapping)

                elif isinstance(content, list):
                    # Handle chat messages
                    for i, message in enumerate(content):
                        if isinstance(message, dict) and "content" in message:
                            anonymized, mapping = self.guard.anonymize(
                                message["content"]
                            )
                            anonymized_body[path][i]["content"] = anonymized
                            combined_mapping.update(mapping)

        return anonymized_body, combined_mapping

    def _deanonymize_response_body(
        self,
        body: Dict,
        mapping: Dict[str, str],
        provider_config: Dict,
    ) -> Dict:
        """
        De-anonymize PII in response body.

        Args:
            body: Response body
            mapping: PII mapping
            provider_config: Provider configuration

        Returns:
            De-anonymized response body
        """
        deanonymized_body = body.copy()

        # Common response paths
        response_paths = [
            ["choices", 0, "message", "content"],
            ["choices", 0, "text"],
            ["content", 0, "text"],
            ["completion"],
        ]

        for path in response_paths:
            try:
                # Navigate to the content
                current = deanonymized_body
                for key in path[:-1]:
                    if isinstance(current, list):
                        current = current[key]
                    elif isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    # De-anonymize if we found the content
                    final_key = path[-1]
                    if isinstance(current, dict) and final_key in current:
                        current[final_key] = self.guard.deanonymize(
                            current[final_key], mapping
                        )
            except (KeyError, IndexError, TypeError):
                continue

        return deanonymized_body

    async def _handle_streaming_response(
        self,
        response: httpx.Response,
        mapping: Dict[str, str],
        session_id: str,
    ) -> StreamingResponse:
        """
        Handle streaming LLM responses.

        Args:
            response: Upstream response
            mapping: PII mapping
            session_id: Session identifier

        Returns:
            Streaming response
        """
        async def stream_generator():
            async for chunk in response.aiter_bytes():
                # Parse SSE chunk
                if chunk.startswith(b"data: "):
                    try:
                        data = json.loads(chunk[6:])

                        # De-anonymize content in chunk
                        if "choices" in data:
                            for choice in data["choices"]:
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    choice["delta"]["content"] = self.guard.deanonymize(
                                        content, mapping
                                    )

                        yield b"data: " + json.dumps(data).encode() + b"\n\n"
                    except json.JSONDecodeError:
                        yield chunk
                else:
                    yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers=dict(response.headers),
        )

    def get_metrics(self) -> Dict:
        """Get proxy metrics."""
        return {
            **self.metrics,
            "storage_health": self.storage.health_check(),
            "rate_limiting_enabled": self.rate_limiter is not None,
        }
    
    def get_rate_limit_status(
        self,
        client_ip: str,
        user_id: Optional[str] = None,
    ) -> Dict:
        """
        Get rate limit status for a client.
        
        Args:
            client_ip: Client IP address
            user_id: Optional user identifier
        
        Returns:
            Rate limit status including remaining requests
        """
        if not self.rate_limiter:
            return {"rate_limiting": "disabled"}
        
        return {
            "rate_limiting": "enabled",
            **self.rate_limiter.get_remaining(client_ip, user_id),
        }


# FastAPI app
app = FastAPI(
    title="LLM PII Protection Proxy",
    description="Transparent HTTP proxy for LLM API calls with automatic PII protection",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global proxy instance
proxy: Optional[LLMProxy] = None


def get_proxy() -> LLMProxy:
    """Get the global proxy instance."""
    if proxy is None:
        raise HTTPException(status_code=500, detail="Proxy not initialized")
    return proxy


@app.on_event("startup")
async def startup():
    """Initialize proxy on startup."""
    global proxy
    config = ProxyConfig()  # Load from environment or config file
    proxy = LLMProxy(config)
    logger.info(
        "Proxy initialized successfully",
        port=config.port,
        host=config.host,
        policy=config.policy,
        rate_limiting_enabled=config.enable_rate_limiting,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def metrics(proxy: LLMProxy = Depends(get_proxy)):
    """Get proxy metrics."""
    return proxy.get_metrics()


@app.get("/ratelimit/status")
async def rate_limit_status(
    request: Request,
    proxy: LLMProxy = Depends(get_proxy),
):
    """Get rate limit status for the current client."""
    client_ip = request.client.host if request.client else "unknown"
    user_id = request.headers.get("X-User-ID")
    return proxy.get_rate_limit_status(client_ip, user_id)


@app.api_route("/openai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def openai_proxy(
    path: str,
    request: Request,
    proxy: LLMProxy = Depends(get_proxy),
):
    """Proxy requests to OpenAI API."""
    return await proxy.proxy_request("openai", f"/{path}", request)


@app.api_route("/anthropic/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def anthropic_proxy(
    path: str,
    request: Request,
    proxy: LLMProxy = Depends(get_proxy),
):
    """Proxy requests to Anthropic API."""
    return await proxy.proxy_request("anthropic", f"/{path}", request)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM PII Protection Proxy")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument(
        "--redis-url",
        type=str,
        default="redis://localhost:6379",
        help="Redis URL for session storage",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="default_pii",
        help="PII protection policy to use",
    )

    args = parser.parse_args()

    # Update global config
    config = ProxyConfig(
        port=args.port,
        host=args.host,
        redis_url=args.redis_url,
        policy=args.policy,
    )

    # Initialize proxy
    proxy = LLMProxy(config)

    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
    )

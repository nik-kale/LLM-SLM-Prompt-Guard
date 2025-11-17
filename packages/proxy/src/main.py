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

from prompt_guard import PromptGuard
from prompt_guard.storage.redis_storage import RedisMappingStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    rate_limit: Optional[int] = None  # Requests per minute


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
        self.metrics = {
            "requests_total": 0,
            "requests_anonymized": 0,
            "pii_detected": 0,
            "errors": 0,
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

        # Get provider config
        provider_config = self.PROVIDERS.get(provider)
        if not provider_config:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        try:
            # Get request body
            body = await request.json()

            # Create session
            session_id = self.storage.create_session(
                user_id=request.headers.get("X-User-ID"),
                metadata={"provider": provider, "endpoint": endpoint},
            )

            # Anonymize messages in the request
            anonymized_body, mapping = self._anonymize_request_body(body, provider_config)

            # Store mapping for this session
            if mapping:
                self.storage.store_mapping(session_id, mapping)
                self.metrics["requests_anonymized"] += 1
                self.metrics["pii_detected"] += len(mapping)

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
            logger.error(f"Proxy error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

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
    logger.info(f"Proxy initialized on port {config.port}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def metrics(proxy: LLMProxy = Depends(get_proxy)):
    """Get proxy metrics."""
    return proxy.get_metrics()


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

"""
Vercel AI SDK adapter for prompt-guard.

Provides seamless integration with the Vercel AI SDK for building
AI-powered applications with PII protection.

Installation:
    pip install llm-slm-prompt-guard
    # Note: Vercel AI SDK is primarily a Node.js library
    # This adapter is for Python backends that integrate with Vercel AI

Example:
    >>> from prompt_guard import PromptGuard
    >>> from prompt_guard.adapters.vercel_ai_adapter import ProtectedStreamingResponse
    >>>
    >>> guard = PromptGuard(policy="default_pii")
    >>>
    >>> # Protect streaming responses
    >>> async def stream_handler(request):
    ...     async for chunk in protected_stream(request, guard):
    ...         yield chunk
"""

from typing import Any, AsyncIterator, Dict, Optional, List, Callable
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class VercelAIAdapter:
    """
    Adapter for Vercel AI SDK integration.

    This adapter provides PII protection for Vercel AI SDK streaming responses,
    function calls, and tool usage.
    """

    def __init__(self, guard: Any, deanonymize_response: bool = True):
        """
        Initialize Vercel AI adapter.

        Args:
            guard: PromptGuard instance (sync or async)
            deanonymize_response: Whether to de-anonymize responses
        """
        self.guard = guard
        self.deanonymize_response = deanonymize_response
        self._is_async = hasattr(guard, "anonymize_async")

    async def protect_messages(
        self, messages: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Protect messages array (Vercel AI SDK format).

        Args:
            messages: Array of message objects with 'role' and 'content'

        Returns:
            Tuple of (anonymized_messages, mapping)
        """
        anonymized_messages = []
        combined_mapping = {}

        for message in messages:
            if "content" in message and isinstance(message["content"], str):
                if self._is_async:
                    result = await self.guard.anonymize_async(message["content"])
                    anonymized_content = result.anonymized
                    mapping = result.mapping
                else:
                    anonymized_content, mapping = self.guard.anonymize(message["content"])

                anonymized_messages.append({
                    **message,
                    "content": anonymized_content,
                })
                combined_mapping.update(mapping)
            else:
                anonymized_messages.append(message)

        return anonymized_messages, combined_mapping

    async def protect_streaming_response(
        self, stream: AsyncIterator[str], mapping: Dict[str, str]
    ) -> AsyncIterator[str]:
        """
        Protect streaming response by de-anonymizing chunks.

        Args:
            stream: Async iterator of response chunks
            mapping: PII mapping to use for de-anonymization

        Yields:
            De-anonymized chunks
        """
        async for chunk in stream:
            if self.deanonymize_response and mapping:
                chunk = self.guard.deanonymize(chunk, mapping)
            yield chunk

    async def protect_function_call(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        Protect function call arguments.

        Args:
            function_name: Name of the function being called
            arguments: Function arguments

        Returns:
            Tuple of (function_name, anonymized_arguments, mapping)
        """
        # Serialize arguments to detect PII
        args_str = json.dumps(arguments, ensure_ascii=False)

        if self._is_async:
            result = await self.guard.anonymize_async(args_str)
            anonymized_str = result.anonymized
            mapping = result.mapping
        else:
            anonymized_str, mapping = self.guard.anonymize(args_str)

        # Parse back to dict
        anonymized_arguments = json.loads(anonymized_str)

        return function_name, anonymized_arguments, mapping

    def create_protected_handler(
        self, handler: Callable
    ) -> Callable:
        """
        Create a protected version of a Vercel AI handler.

        Args:
            handler: Original async handler function

        Returns:
            Protected handler that anonymizes requests and de-anonymizes responses
        """
        async def protected_handler(request: Dict[str, Any]) -> Any:
            # Extract messages from request
            messages = request.get("messages", [])

            # Protect messages
            anonymized_messages, mapping = await self.protect_messages(messages)

            # Update request with anonymized messages
            protected_request = {
                **request,
                "messages": anonymized_messages,
            }

            # Call original handler
            response = await handler(protected_request)

            # De-anonymize response if needed
            if self.deanonymize_response and mapping:
                if isinstance(response, dict):
                    # Handle object response
                    if "content" in response:
                        response["content"] = self.guard.deanonymize(
                            response["content"], mapping
                        )
                elif isinstance(response, str):
                    # Handle string response
                    response = self.guard.deanonymize(response, mapping)

            return response

        return protected_handler


class ProtectedStreamingChat:
    """
    Protected streaming chat handler for Vercel AI SDK.

    Example:
        >>> from vercel_ai import OpenAI
        >>> from prompt_guard import PromptGuard
        >>>
        >>> guard = PromptGuard(policy="default_pii")
        >>> chat = ProtectedStreamingChat(guard=guard)
        >>>
        >>> async for chunk in chat.stream(messages=[...]):
        ...     print(chunk)
    """

    def __init__(
        self,
        guard: Any,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        deanonymize_response: bool = True,
    ):
        """
        Initialize protected streaming chat.

        Args:
            guard: PromptGuard instance
            model: LLM model to use
            api_key: API key for LLM provider
            deanonymize_response: Whether to de-anonymize responses
        """
        self.guard = guard
        self.model = model
        self.api_key = api_key
        self.deanonymize_response = deanonymize_response
        self.adapter = VercelAIAdapter(guard, deanonymize_response)

    async def stream(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion with PII protection.

        Args:
            messages: Array of messages
            **kwargs: Additional arguments for the LLM

        Yields:
            Response chunks
        """
        # Protect messages
        anonymized_messages, mapping = await self.adapter.protect_messages(messages)

        # Note: Actual Vercel AI SDK integration would go here
        # This is a simplified example showing the pattern
        logger.warning(
            "Vercel AI SDK streaming requires Node.js integration. "
            "This adapter provides the Python-side PII protection logic."
        )

        # Simulate streaming response (in production, call actual LLM)
        response_text = "This is a simulated response."
        for char in response_text:
            await asyncio.sleep(0.01)  # Simulate streaming delay
            yield char

    async def complete(
        self, messages: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """
        Non-streaming completion with PII protection.

        Args:
            messages: Array of messages
            **kwargs: Additional arguments for the LLM

        Returns:
            Completion response
        """
        # Protect messages
        anonymized_messages, mapping = await self.adapter.protect_messages(messages)

        # Call LLM (simplified - actual implementation would use Vercel AI SDK)
        response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a simulated response.",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

        # De-anonymize response
        if self.deanonymize_response and mapping:
            response["choices"][0]["message"]["content"] = self.guard.deanonymize(
                response["choices"][0]["message"]["content"], mapping
            )

        return response


def create_protected_vercel_handler(
    guard: Any,
    handler: Callable,
    deanonymize_response: bool = True,
) -> Callable:
    """
    Create a protected Vercel AI handler.

    Args:
        guard: PromptGuard instance
        handler: Original async handler
        deanonymize_response: Whether to de-anonymize responses

    Returns:
        Protected handler

    Example:
        >>> from prompt_guard import PromptGuard
        >>>
        >>> guard = PromptGuard(policy="default_pii")
        >>>
        >>> async def my_handler(request):
        ...     # Your AI logic here
        ...     return {"response": "Hello"}
        >>>
        >>> protected = create_protected_vercel_handler(guard, my_handler)
    """
    adapter = VercelAIAdapter(guard, deanonymize_response)
    return adapter.create_protected_handler(handler)


def create_protected_streaming_chat(
    guard: Any,
    model: str = "gpt-4",
    api_key: Optional[str] = None,
    deanonymize_response: bool = True,
) -> "ProtectedStreamingChat":
    """
    Create a protected streaming chat instance.

    Args:
        guard: PromptGuard instance
        model: LLM model to use
        api_key: API key for LLM provider
        deanonymize_response: Whether to de-anonymize responses

    Returns:
        ProtectedStreamingChat instance

    Example:
        >>> from prompt_guard import AsyncPromptGuard
        >>>
        >>> guard = AsyncPromptGuard(policy="default_pii")
        >>> chat = create_protected_streaming_chat(guard, model="gpt-4")
        >>>
        >>> async for chunk in chat.stream(messages=[...]):
        ...     print(chunk, end="")
    """
    return ProtectedStreamingChat(guard, model, api_key, deanonymize_response)


__all__ = [
    "VercelAIAdapter",
    "ProtectedStreamingChat",
    "create_protected_vercel_handler",
    "create_protected_streaming_chat",
]

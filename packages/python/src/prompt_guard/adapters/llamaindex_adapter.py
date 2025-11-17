"""
LlamaIndex adapter for PromptGuard.

Provides seamless integration with LlamaIndex query engines and chat engines,
automatically anonymizing queries and de-anonymizing responses.
"""

from typing import Any, List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

try:
    from llama_index.core.base.base_query_engine import BaseQueryEngine
    from llama_index.core.base.response.schema import Response, StreamingResponse
    from llama_index.core.chat_engine.types import BaseChatEngine
    from llama_index.core.schema import QueryBundle

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    try:
        # Try older import path
        from llama_index import BaseQueryEngine, Response, StreamingResponse

        LLAMAINDEX_AVAILABLE = True
    except ImportError:
        LLAMAINDEX_AVAILABLE = False
        logger.warning("LlamaIndex not available. Install with: pip install llama-index")


if LLAMAINDEX_AVAILABLE:

    class ProtectedQueryEngine:
        """
        LlamaIndex QueryEngine wrapper that anonymizes PII before querying.

        Example:
            >>> from llama_index import VectorStoreIndex, SimpleDirectoryReader
            >>> from prompt_guard import PromptGuard
            >>> from prompt_guard.adapters import ProtectedQueryEngine
            >>>
            >>> documents = SimpleDirectoryReader('data').load_data()
            >>> index = VectorStoreIndex.from_documents(documents)
            >>> query_engine = index.as_query_engine()
            >>>
            >>> guard = PromptGuard(policy="default_pii")
            >>> protected_engine = ProtectedQueryEngine(query_engine, guard)
            >>>
            >>> # Query with PII
            >>> response = protected_engine.query("What's the email for John Smith?")
            >>> # PII is automatically protected!
        """

        def __init__(
            self,
            query_engine: Any,  # BaseQueryEngine
            guard: Any,  # PromptGuard
            deanonymize_response: bool = True,
            store_mappings: bool = False,
        ):
            """
            Initialize protected query engine.

            Args:
                query_engine: The underlying LlamaIndex query engine
                guard: PromptGuard instance
                deanonymize_response: Whether to de-anonymize responses
                store_mappings: Whether to store mappings for later retrieval
            """
            self.query_engine = query_engine
            self.guard = guard
            self.deanonymize_response = deanonymize_response
            self.store_mappings = store_mappings
            self._mappings: Dict[str, Dict[str, str]] = {}

        def query(self, query: str) -> Any:
            """
            Query with PII protection.

            Args:
                query: The query string

            Returns:
                Query response (de-anonymized if enabled)
            """
            # Anonymize the query
            anonymized_query, mapping = self.guard.anonymize(query)

            # Store mapping if requested
            if self.store_mappings:
                self._mappings[query] = mapping

            # Query the underlying engine
            response = self.query_engine.query(anonymized_query)

            # De-anonymize the response if enabled
            if self.deanonymize_response and mapping:
                if hasattr(response, "response"):
                    response.response = self.guard.deanonymize(
                        response.response, mapping
                    )

                # Also de-anonymize source nodes if present
                if hasattr(response, "source_nodes"):
                    for node in response.source_nodes:
                        if hasattr(node, "text"):
                            node.text = self.guard.deanonymize(node.text, mapping)

            return response

        async def aquery(self, query: str) -> Any:
            """
            Async query with PII protection.

            Args:
                query: The query string

            Returns:
                Query response (de-anonymized if enabled)
            """
            # Anonymize the query
            anonymized_query, mapping = self.guard.anonymize(query)

            # Store mapping if requested
            if self.store_mappings:
                self._mappings[query] = mapping

            # Query the underlying engine asynchronously
            if hasattr(self.query_engine, "aquery"):
                response = await self.query_engine.aquery(anonymized_query)
            else:
                # Fallback to sync if async not supported
                response = self.query_engine.query(anonymized_query)

            # De-anonymize the response
            if self.deanonymize_response and mapping:
                if hasattr(response, "response"):
                    response.response = self.guard.deanonymize(
                        response.response, mapping
                    )

            return response

        def get_mapping(self, query: str) -> Optional[Dict[str, str]]:
            """Get the PII mapping for a specific query."""
            return self._mappings.get(query)

        def clear_mappings(self) -> None:
            """Clear all stored mappings."""
            self._mappings.clear()

    class ProtectedChatEngine:
        """
        LlamaIndex ChatEngine wrapper with PII protection.

        Example:
            >>> from llama_index import VectorStoreIndex
            >>> from prompt_guard import PromptGuard
            >>> from prompt_guard.adapters import ProtectedChatEngine
            >>>
            >>> index = VectorStoreIndex.from_documents(documents)
            >>> chat_engine = index.as_chat_engine()
            >>>
            >>> guard = PromptGuard(policy="default_pii")
            >>> protected_chat = ProtectedChatEngine(chat_engine, guard)
            >>>
            >>> # Chat with PII
            >>> response = protected_chat.chat("My email is john@example.com")
        """

        def __init__(
            self,
            chat_engine: Any,  # BaseChatEngine
            guard: Any,  # PromptGuard
            deanonymize_response: bool = True,
        ):
            """
            Initialize protected chat engine.

            Args:
                chat_engine: The underlying LlamaIndex chat engine
                guard: PromptGuard instance
                deanonymize_response: Whether to de-anonymize responses
            """
            self.chat_engine = chat_engine
            self.guard = guard
            self.deanonymize_response = deanonymize_response
            self._conversation_mapping: Dict[str, str] = {}

        def chat(self, message: str) -> Any:
            """
            Chat with PII protection.

            Args:
                message: Chat message

            Returns:
                Chat response
            """
            # Anonymize the message
            anonymized_message, mapping = self.guard.anonymize(message)

            # Update conversation mapping (accumulate across turns)
            self._conversation_mapping.update(mapping)

            # Chat with the underlying engine
            response = self.chat_engine.chat(anonymized_message)

            # De-anonymize the response if enabled
            if self.deanonymize_response and self._conversation_mapping:
                if hasattr(response, "response"):
                    response.response = self.guard.deanonymize(
                        response.response, self._conversation_mapping
                    )

            return response

        async def achat(self, message: str) -> Any:
            """
            Async chat with PII protection.

            Args:
                message: Chat message

            Returns:
                Chat response
            """
            # Anonymize the message
            anonymized_message, mapping = self.guard.anonymize(message)

            # Update conversation mapping
            self._conversation_mapping.update(mapping)

            # Chat with the underlying engine asynchronously
            if hasattr(self.chat_engine, "achat"):
                response = await self.chat_engine.achat(anonymized_message)
            else:
                # Fallback to sync if async not supported
                response = self.chat_engine.chat(anonymized_message)

            # De-anonymize the response
            if self.deanonymize_response and self._conversation_mapping:
                if hasattr(response, "response"):
                    response.response = self.guard.deanonymize(
                        response.response, self._conversation_mapping
                    )

            return response

        def reset(self) -> None:
            """Reset conversation history and mappings."""
            if hasattr(self.chat_engine, "reset"):
                self.chat_engine.reset()
            self._conversation_mapping.clear()

        def stream_chat(self, message: str) -> Any:
            """
            Stream chat with PII protection.

            Args:
                message: Chat message

            Returns:
                Streaming response
            """
            # Anonymize the message
            anonymized_message, mapping = self.guard.anonymize(message)

            # Update conversation mapping
            self._conversation_mapping.update(mapping)

            # Stream chat with the underlying engine
            if hasattr(self.chat_engine, "stream_chat"):
                response = self.chat_engine.stream_chat(anonymized_message)

                # Wrap the streaming response to de-anonymize chunks
                if self.deanonymize_response and self._conversation_mapping:
                    return self._deanonymize_stream(response)

                return response
            else:
                raise NotImplementedError("Chat engine does not support streaming")

        def _deanonymize_stream(self, stream):
            """Wrap a streaming response to de-anonymize chunks."""
            for chunk in stream:
                if hasattr(chunk, "response"):
                    chunk.response = self.guard.deanonymize(
                        chunk.response, self._conversation_mapping
                    )
                yield chunk


def create_protected_query_engine(
    query_engine: Any,
    guard: Any,
    **kwargs: Any,
) -> ProtectedQueryEngine:
    """
    Create a protected LlamaIndex query engine.

    Args:
        query_engine: The underlying query engine
        guard: PromptGuard instance
        **kwargs: Additional arguments

    Returns:
        Protected query engine instance
    """
    if not LLAMAINDEX_AVAILABLE:
        raise ImportError(
            "LlamaIndex is not available. Install with: pip install llama-index"
        )

    return ProtectedQueryEngine(query_engine=query_engine, guard=guard, **kwargs)


def create_protected_chat_engine(
    chat_engine: Any,
    guard: Any,
    **kwargs: Any,
) -> ProtectedChatEngine:
    """
    Create a protected LlamaIndex chat engine.

    Args:
        chat_engine: The underlying chat engine
        guard: PromptGuard instance
        **kwargs: Additional arguments

    Returns:
        Protected chat engine instance
    """
    if not LLAMAINDEX_AVAILABLE:
        raise ImportError(
            "LlamaIndex is not available. Install with: pip install llama-index"
        )

    return ProtectedChatEngine(chat_engine=chat_engine, guard=guard, **kwargs)

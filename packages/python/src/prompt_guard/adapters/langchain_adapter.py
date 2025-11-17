"""
LangChain adapter for PromptGuard.

Provides seamless integration with LangChain LLMs and chains,
automatically anonymizing prompts and de-anonymizing responses.
"""

from typing import Any, List, Optional, Dict, Mapping as TypeMapping
import logging

logger = logging.getLogger(__name__)

try:
    from langchain.llms.base import LLM
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. Install with: pip install langchain")


if LANGCHAIN_AVAILABLE:
    class ProtectedLLM(LLM):
        """
        LangChain LLM wrapper that anonymizes PII before sending to the underlying LLM.

        Example:
            >>> from langchain.llms import OpenAI
            >>> from prompt_guard import PromptGuard
            >>> from prompt_guard.adapters import ProtectedLLM
            >>>
            >>> base_llm = OpenAI(temperature=0.7)
            >>> guard = PromptGuard(policy="default_pii")
            >>> protected_llm = ProtectedLLM(llm=base_llm, guard=guard)
            >>>
            >>> # Use it like any LangChain LLM
            >>> response = protected_llm("My email is john@example.com")
        """

        llm: Any  #: The underlying LLM to wrap
        guard: Any  #: PromptGuard instance
        deanonymize_response: bool = True  #: Whether to de-anonymize responses
        store_mappings: bool = False  #: Whether to store mappings for later retrieval
        _mappings: Dict[str, Dict[str, str]] = {}  #: Internal mapping storage

        @property
        def _llm_type(self) -> str:
            """Return type of underlying LLM."""
            return f"protected_{self.llm._llm_type}"

        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> str:
            """
            Call the LLM with PII protection.

            Args:
                prompt: The prompt to send to the LLM
                stop: Stop sequences
                run_manager: Callback manager
                **kwargs: Additional arguments for the underlying LLM

            Returns:
                The LLM response (de-anonymized if enabled)
            """
            # Anonymize the prompt
            anonymized_prompt, mapping = self.guard.anonymize(prompt)

            # Store mapping if requested
            if self.store_mappings:
                self._mappings[prompt] = mapping

            # Call the underlying LLM
            response = self.llm(
                anonymized_prompt,
                stop=stop,
                callbacks=run_manager.get_child() if run_manager else None,
                **kwargs,
            )

            # De-anonymize the response if enabled
            if self.deanonymize_response and mapping:
                response = self.guard.deanonymize(response, mapping)

            return response

        def get_mapping(self, prompt: str) -> Optional[Dict[str, str]]:
            """
            Get the PII mapping for a specific prompt.

            Args:
                prompt: The original prompt

            Returns:
                The PII mapping, or None if not found/stored
            """
            return self._mappings.get(prompt)

        def clear_mappings(self) -> None:
            """Clear all stored mappings."""
            self._mappings.clear()


    class ProtectedChatLLM:
        """
        Wrapper for LangChain Chat Models with PII protection.

        Example:
            >>> from langchain.chat_models import ChatOpenAI
            >>> from prompt_guard import PromptGuard
            >>> from prompt_guard.adapters import ProtectedChatLLM
            >>>
            >>> chat = ChatOpenAI(temperature=0)
            >>> guard = PromptGuard(policy="default_pii")
            >>> protected_chat = ProtectedChatLLM(chat=chat, guard=guard)
            >>>
            >>> from langchain.schema import HumanMessage
            >>> messages = [HumanMessage(content="Email: john@example.com")]
            >>> response = protected_chat(messages)
        """

        def __init__(
            self,
            chat: Any,
            guard: Any,
            deanonymize_response: bool = True,
        ):
            """
            Initialize protected chat LLM.

            Args:
                chat: The underlying chat model
                guard: PromptGuard instance
                deanonymize_response: Whether to de-anonymize responses
            """
            self.chat = chat
            self.guard = guard
            self.deanonymize_response = deanonymize_response

        def __call__(self, messages: List[Any], **kwargs: Any) -> Any:
            """
            Call the chat model with PII protection.

            Args:
                messages: List of messages
                **kwargs: Additional arguments

            Returns:
                Chat model response
            """
            from langchain.schema import HumanMessage, AIMessage, SystemMessage

            # Anonymize messages
            anonymized_messages = []
            mappings = []

            for message in messages:
                content = message.content
                anonymized_content, mapping = self.guard.anonymize(content)
                mappings.append(mapping)

                # Preserve message type
                if isinstance(message, HumanMessage):
                    anonymized_messages.append(
                        HumanMessage(content=anonymized_content)
                    )
                elif isinstance(message, AIMessage):
                    anonymized_messages.append(
                        AIMessage(content=anonymized_content)
                    )
                elif isinstance(message, SystemMessage):
                    anonymized_messages.append(
                        SystemMessage(content=anonymized_content)
                    )
                else:
                    anonymized_messages.append(message)

            # Call underlying chat model
            response = self.chat(anonymized_messages, **kwargs)

            # De-anonymize response if enabled
            if self.deanonymize_response and mappings:
                # Combine all mappings
                combined_mapping = {}
                for mapping in mappings:
                    combined_mapping.update(mapping)

                if hasattr(response, 'content'):
                    response.content = self.guard.deanonymize(
                        response.content, combined_mapping
                    )

            return response


def create_protected_llm(
    llm: Any,
    guard: Any,
    **kwargs: Any,
) -> "ProtectedLLM":
    """
    Create a protected LangChain LLM.

    Args:
        llm: The underlying LLM
        guard: PromptGuard instance
        **kwargs: Additional arguments

    Returns:
        Protected LLM instance
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is not available. Install with: pip install langchain"
        )

    return ProtectedLLM(llm=llm, guard=guard, **kwargs)


def create_protected_chat(
    chat: Any,
    guard: Any,
    **kwargs: Any,
) -> "ProtectedChatLLM":
    """
    Create a protected LangChain chat model.

    Args:
        chat: The underlying chat model
        guard: PromptGuard instance
        **kwargs: Additional arguments

    Returns:
        Protected chat model instance
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is not available. Install with: pip install langchain"
        )

    return ProtectedChatLLM(chat=chat, guard=guard, **kwargs)

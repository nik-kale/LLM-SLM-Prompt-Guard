"""
Hugging Face Transformers adapter for prompt-guard.

Provides seamless integration with Hugging Face models for text generation,
chat, and other NLP tasks with automatic PII protection.

Installation:
    pip install llm-slm-prompt-guard transformers torch

Example:
    >>> from transformers import pipeline
    >>> from prompt_guard import PromptGuard
    >>> from prompt_guard.adapters import create_protected_pipeline
    >>>
    >>> base_pipeline = pipeline("text-generation", model="gpt2")
    >>> guard = PromptGuard(policy="default_pii")
    >>> protected_pipeline = create_protected_pipeline(base_pipeline, guard)
    >>>
    >>> result = protected_pipeline("My email is john@example.com")
    >>> # PII is automatically protected!
"""

from typing import Any, Dict, List, Optional, Union, Callable
import logging

logger = logging.getLogger(__name__)


class ProtectedPipeline:
    """
    Protected Hugging Face pipeline wrapper.

    Automatically anonymizes inputs before sending to the model and
    de-anonymizes outputs before returning to the user.

    Example:
        >>> from transformers import pipeline
        >>> from prompt_guard import PromptGuard
        >>>
        >>> pipe = pipeline("text-generation", model="gpt2")
        >>> guard = PromptGuard(policy="default_pii")
        >>>
        >>> protected = ProtectedPipeline(pipe, guard)
        >>> result = protected("Contact me at john@example.com")
    """

    def __init__(
        self,
        pipeline: Any,
        guard: Any,
        deanonymize_output: bool = True,
        store_mapping: bool = False,
    ):
        """
        Initialize protected pipeline.

        Args:
            pipeline: Hugging Face pipeline instance
            guard: PromptGuard instance
            deanonymize_output: Whether to de-anonymize outputs
            store_mapping: Whether to store mappings for later use
        """
        self.pipeline = pipeline
        self.guard = guard
        self.deanonymize_output = deanonymize_output
        self.store_mapping = store_mapping
        self._last_mapping: Optional[Dict[str, str]] = None

    def __call__(
        self, inputs: Union[str, List[str]], **kwargs
    ) -> Union[Any, List[Any]]:
        """
        Run pipeline with PII protection.

        Args:
            inputs: Text input(s)
            **kwargs: Additional pipeline arguments

        Returns:
            Protected pipeline output(s)
        """
        is_batch = isinstance(inputs, list)

        # Anonymize inputs
        if is_batch:
            anonymized_inputs = []
            mappings = []
            for text in inputs:
                anonymized, mapping = self.guard.anonymize(text)
                anonymized_inputs.append(anonymized)
                mappings.append(mapping)
        else:
            anonymized_inputs, mapping = self.guard.anonymize(inputs)
            mappings = [mapping]

        # Store mapping for later retrieval
        if self.store_mapping:
            if is_batch:
                # For batch, store combined mapping
                self._last_mapping = {}
                for m in mappings:
                    self._last_mapping.update(m)
            else:
                self._last_mapping = mapping

        # Run pipeline
        outputs = self.pipeline(anonymized_inputs, **kwargs)

        # De-anonymize outputs
        if self.deanonymize_output:
            if is_batch:
                deanonymized_outputs = []
                for output, mapping in zip(outputs, mappings):
                    deanonymized = self._deanonymize_output(output, mapping)
                    deanonymized_outputs.append(deanonymized)
                return deanonymized_outputs
            else:
                return self._deanonymize_output(outputs, mapping)

        return outputs

    def _deanonymize_output(self, output: Any, mapping: Dict[str, str]) -> Any:
        """De-anonymize pipeline output."""
        if not mapping:
            return output

        # Handle different output formats
        if isinstance(output, list):
            # List of outputs (e.g., text generation)
            return [self._deanonymize_output(item, mapping) for item in output]
        elif isinstance(output, dict):
            # Dict output (e.g., with scores)
            if "generated_text" in output:
                output["generated_text"] = self.guard.deanonymize(
                    output["generated_text"], mapping
                )
            elif "summary_text" in output:
                output["summary_text"] = self.guard.deanonymize(
                    output["summary_text"], mapping
                )
            elif "translation_text" in output:
                output["translation_text"] = self.guard.deanonymize(
                    output["translation_text"], mapping
                )
            # Handle other text fields
            for key in output:
                if isinstance(output[key], str):
                    output[key] = self.guard.deanonymize(output[key], mapping)
            return output
        elif isinstance(output, str):
            # String output
            return self.guard.deanonymize(output, mapping)

        return output

    def get_last_mapping(self) -> Optional[Dict[str, str]]:
        """Get the mapping from the last call."""
        return self._last_mapping

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying pipeline."""
        return getattr(self.pipeline, name)


class ProtectedConversational:
    """
    Protected conversational pipeline for multi-turn conversations.

    Maintains conversation history with PII protection across turns.

    Example:
        >>> from transformers import pipeline, Conversation
        >>> from prompt_guard import PromptGuard
        >>>
        >>> pipe = pipeline("conversational", model="facebook/blenderbot-400M-distill")
        >>> guard = PromptGuard(policy="default_pii")
        >>>
        >>> protected = ProtectedConversational(pipe, guard)
        >>> conversation = Conversation("My email is john@example.com")
        >>> result = protected(conversation)
    """

    def __init__(
        self,
        pipeline: Any,
        guard: Any,
        deanonymize_output: bool = True,
    ):
        """
        Initialize protected conversational pipeline.

        Args:
            pipeline: Conversational pipeline
            guard: PromptGuard instance
            deanonymize_output: Whether to de-anonymize outputs
        """
        self.pipeline = pipeline
        self.guard = guard
        self.deanonymize_output = deanonymize_output
        self._conversation_mappings: Dict[str, Dict[str, str]] = {}

    def __call__(self, conversations: Any, **kwargs) -> Any:
        """
        Run conversational pipeline with PII protection.

        Args:
            conversations: Conversation object or list of conversations
            **kwargs: Additional pipeline arguments

        Returns:
            Protected conversation output(s)
        """
        from transformers import Conversation

        is_batch = isinstance(conversations, list)
        convs_to_process = conversations if is_batch else [conversations]

        # Anonymize conversations
        anonymized_convs = []
        for conv in convs_to_process:
            conv_id = id(conv)

            # Initialize mapping for new conversations
            if conv_id not in self._conversation_mappings:
                self._conversation_mappings[conv_id] = {}

            # Anonymize new messages
            new_messages = []
            for message in conv.iter_texts():
                anonymized, mapping = self.guard.anonymize(message)
                new_messages.append(anonymized)
                # Accumulate mappings across conversation
                self._conversation_mappings[conv_id].update(mapping)

            # Create anonymized conversation
            anonymized_conv = Conversation()
            for msg in new_messages:
                anonymized_conv.add_user_input(msg)

            anonymized_convs.append(anonymized_conv)

        # Run pipeline
        if is_batch:
            outputs = self.pipeline(anonymized_convs, **kwargs)
        else:
            outputs = self.pipeline(anonymized_convs[0], **kwargs)

        # De-anonymize outputs
        if self.deanonymize_output:
            output_convs = outputs if is_batch else [outputs]
            for i, (conv, orig_conv) in enumerate(zip(output_convs, convs_to_process)):
                conv_id = id(orig_conv)
                mapping = self._conversation_mappings.get(conv_id, {})

                # De-anonymize generated responses
                if hasattr(conv, "generated_responses"):
                    conv.generated_responses = [
                        self.guard.deanonymize(resp, mapping)
                        for resp in conv.generated_responses
                    ]

        return outputs

    def reset_conversation(self, conversation: Any) -> None:
        """Reset conversation mapping."""
        conv_id = id(conversation)
        if conv_id in self._conversation_mappings:
            del self._conversation_mappings[conv_id]


class ProtectedTextGeneration:
    """
    Protected text generation for Hugging Face models.

    Works with model.generate() for more control over generation.

    Example:
        >>> from transformers import AutoTokenizer, AutoModelForCausalLM
        >>> from prompt_guard import PromptGuard
        >>>
        >>> tokenizer = AutoTokenizer.from_pretrained("gpt2")
        >>> model = AutoModelForCausalLM.from_pretrained("gpt2")
        >>> guard = PromptGuard(policy="default_pii")
        >>>
        >>> protected = ProtectedTextGeneration(model, tokenizer, guard)
        >>> result = protected.generate("My email is john@example.com")
    """

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        guard: Any,
        deanonymize_output: bool = True,
    ):
        """
        Initialize protected text generation.

        Args:
            model: Hugging Face model
            tokenizer: Hugging Face tokenizer
            guard: PromptGuard instance
            deanonymize_output: Whether to de-anonymize outputs
        """
        self.model = model
        self.tokenizer = tokenizer
        self.guard = guard
        self.deanonymize_output = deanonymize_output

    def generate(
        self, prompt: Union[str, List[str]], **kwargs
    ) -> Union[str, List[str]]:
        """
        Generate text with PII protection.

        Args:
            prompt: Input prompt(s)
            **kwargs: Generation arguments (max_length, temperature, etc.)

        Returns:
            Generated text(s)
        """
        is_batch = isinstance(prompt, list)
        prompts = prompt if is_batch else [prompt]

        # Anonymize prompts
        anonymized_prompts = []
        mappings = []
        for p in prompts:
            anonymized, mapping = self.guard.anonymize(p)
            anonymized_prompts.append(anonymized)
            mappings.append(mapping)

        # Tokenize
        inputs = self.tokenizer(
            anonymized_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )

        # Generate
        outputs = self.model.generate(**inputs, **kwargs)

        # Decode
        generated_texts = self.tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )

        # De-anonymize
        if self.deanonymize_output:
            deanonymized = []
            for text, mapping in zip(generated_texts, mappings):
                deanonymized.append(self.guard.deanonymize(text, mapping))
            generated_texts = deanonymized

        return generated_texts if is_batch else generated_texts[0]


def create_protected_pipeline(
    pipeline: Any,
    guard: Any,
    deanonymize_output: bool = True,
    store_mapping: bool = False,
) -> ProtectedPipeline:
    """
    Create a protected Hugging Face pipeline.

    Args:
        pipeline: Hugging Face pipeline instance
        guard: PromptGuard instance
        deanonymize_output: Whether to de-anonymize outputs
        store_mapping: Whether to store mappings

    Returns:
        ProtectedPipeline instance

    Example:
        >>> from transformers import pipeline
        >>> from prompt_guard import PromptGuard
        >>>
        >>> pipe = pipeline("text-generation", model="gpt2")
        >>> guard = PromptGuard(policy="default_pii")
        >>> protected = create_protected_pipeline(pipe, guard)
    """
    return ProtectedPipeline(pipeline, guard, deanonymize_output, store_mapping)


def create_protected_conversational(
    pipeline: Any,
    guard: Any,
    deanonymize_output: bool = True,
) -> ProtectedConversational:
    """
    Create a protected conversational pipeline.

    Args:
        pipeline: Conversational pipeline
        guard: PromptGuard instance
        deanonymize_output: Whether to de-anonymize outputs

    Returns:
        ProtectedConversational instance

    Example:
        >>> from transformers import pipeline
        >>> from prompt_guard import PromptGuard
        >>>
        >>> pipe = pipeline("conversational")
        >>> guard = PromptGuard(policy="default_pii")
        >>> protected = create_protected_conversational(pipe, guard)
    """
    return ProtectedConversational(pipeline, guard, deanonymize_output)


def create_protected_text_generation(
    model: Any,
    tokenizer: Any,
    guard: Any,
    deanonymize_output: bool = True,
) -> ProtectedTextGeneration:
    """
    Create a protected text generation instance.

    Args:
        model: Hugging Face model
        tokenizer: Hugging Face tokenizer
        guard: PromptGuard instance
        deanonymize_output: Whether to de-anonymize outputs

    Returns:
        ProtectedTextGeneration instance

    Example:
        >>> from transformers import AutoTokenizer, AutoModelForCausalLM
        >>> from prompt_guard import PromptGuard
        >>>
        >>> tokenizer = AutoTokenizer.from_pretrained("gpt2")
        >>> model = AutoModelForCausalLM.from_pretrained("gpt2")
        >>> guard = PromptGuard(policy="default_pii")
        >>>
        >>> protected = create_protected_text_generation(model, tokenizer, guard)
    """
    return ProtectedTextGeneration(model, tokenizer, guard, deanonymize_output)


__all__ = [
    "ProtectedPipeline",
    "ProtectedConversational",
    "ProtectedTextGeneration",
    "create_protected_pipeline",
    "create_protected_conversational",
    "create_protected_text_generation",
]

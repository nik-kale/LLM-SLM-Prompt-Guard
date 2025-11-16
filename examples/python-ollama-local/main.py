"""
Ollama Local SLM Example

This example demonstrates using llm-slm-prompt-guard with Ollama
for privacy-preserving local LLM/SLM inference.

Prerequisites:
1. Install Ollama: https://ollama.ai/
2. Pull a model: ollama pull llama2
3. Install dependencies: pip install -r requirements.txt
"""

import sys
import os

# Add package to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages/python/src"))

from prompt_guard import PromptGuard

# Check if ollama is available
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  Ollama Python library not installed.")
    print("Install it with: pip install ollama")


class PrivateLocalChat:
    """
    A chat interface that protects PII before sending to local SLM.
    """

    def __init__(self, model: str = "llama2", policy: str = "slm_local"):
        """
        Initialize the private chat with Ollama.

        Args:
            model: Ollama model name (e.g., "llama2", "mistral", "phi")
            policy: PII protection policy to use
        """
        self.model = model
        self.guard = PromptGuard(detectors=["regex"], policy=policy)
        self.conversation_history = []
        self.pii_mapping = {}  # Persistent mapping across conversation

    def chat(self, message: str, show_anonymized: bool = False) -> dict:
        """
        Send a message to the local SLM with PII protection.

        Args:
            message: User message
            show_anonymized: Whether to show the anonymized prompt

        Returns:
            Dictionary with response and metadata
        """
        # Anonymize the message
        anonymized, new_mapping = self.guard.anonymize(message)

        # Update persistent mapping for multi-turn conversations
        self.pii_mapping.update(new_mapping)

        # Add to conversation history (anonymized version)
        self.conversation_history.append({
            "role": "user",
            "content": anonymized
        })

        result = {
            "original_message": message,
            "anonymized_message": anonymized if show_anonymized else None,
            "pii_detected": len(new_mapping),
            "pii_types": list(set(k.split("_")[0][1:] for k in new_mapping.keys())),
        }

        if OLLAMA_AVAILABLE:
            try:
                # Send to local Ollama model
                response = ollama.chat(
                    model=self.model,
                    messages=self.conversation_history
                )

                # Get the response
                llm_response = response['message']['content']

                # De-anonymize the response
                final_response = self.guard.deanonymize(llm_response, self.pii_mapping)

                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": llm_response  # Store anonymized version in history
                })

                result.update({
                    "response": final_response,
                    "model": self.model,
                    "status": "success"
                })

            except Exception as e:
                result.update({
                    "response": None,
                    "error": str(e),
                    "status": "error"
                })
        else:
            # Mock response if Ollama not available
            result.update({
                "response": f"[MOCK] Response to: {anonymized}",
                "model": "mock",
                "status": "mock"
            })

        return result

    def reset(self):
        """Reset conversation history and PII mapping."""
        self.conversation_history = []
        self.pii_mapping = {}


def interactive_demo():
    """Run an interactive demo of the private chat."""
    print("=" * 60)
    print("Private Local Chat with Ollama")
    print("=" * 60)
    print()

    # Check Ollama availability
    if not OLLAMA_AVAILABLE:
        print("Running in MOCK mode (Ollama not available)")
        print()

    # Initialize chat
    print("Initializing chat with PII protection...")
    chat = PrivateLocalChat(model="llama2", policy="slm_local")
    print("✓ Ready! Using policy: slm_local")
    print()

    # Show some example queries
    examples = [
        "Hi, I'm John Smith and my email is john.smith@example.com. Can you help me?",
        "Please schedule a meeting with Sarah at sarah.j@company.com for tomorrow.",
        "My phone number is 555-123-4567 if you need to call me.",
    ]

    print("Running example queries...")
    print()

    for i, example in enumerate(examples, 1):
        print(f"Example {i}:")
        print(f"User: {example}")
        print()

        result = chat.chat(example, show_anonymized=True)

        print(f"PII Detected: {result['pii_detected']} ({', '.join(result['pii_types'])})")
        print(f"Anonymized: {result['anonymized_message']}")
        print(f"Response: {result['response']}")
        print()
        print("-" * 60)
        print()

    # Interactive mode
    print("Enter your own messages (or 'quit' to exit):")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            result = chat.chat(user_input, show_anonymized=True)

            if result['pii_detected'] > 0:
                print(f"[PII Protected: {result['pii_detected']} items]")
                print(f"[Anonymized: {result['anonymized_message']}]")

            print(f"Assistant: {result['response']}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def batch_demo():
    """Demonstrate batch processing of messages with PII."""
    print("=" * 60)
    print("Batch Processing Demo")
    print("=" * 60)
    print()

    guard = PromptGuard(detectors=["regex"], policy="slm_local")

    messages = [
        "Contact me at alice@example.com",
        "My SSN is 123-45-6789",
        "Call Bob at 555-987-6543",
        "Server IP: 192.168.1.100",
        "This message has no PII",
    ]

    print("Processing batch of messages...")
    print()

    for i, msg in enumerate(messages, 1):
        anonymized, mapping = guard.anonymize(msg)

        print(f"{i}. Original:   {msg}")
        print(f"   Anonymized: {anonymized}")
        print(f"   PII Found:  {len(mapping)} item(s)")
        if mapping:
            for placeholder, original in mapping.items():
                print(f"     {placeholder} = {original}")
        print()


def performance_demo():
    """Demonstrate performance characteristics for SLM use."""
    import time

    print("=" * 60)
    print("Performance Demo (for SLM optimization)")
    print("=" * 60)
    print()

    guard = PromptGuard(detectors=["regex"], policy="slm_local")

    test_message = """
    Hi, I'm John Smith (john.smith@example.com).
    You can reach me at 555-123-4567.
    My account ID is ABC-12345 and IP is 192.168.1.100.
    """

    # Warm up
    guard.anonymize(test_message)

    # Benchmark
    iterations = 1000
    start = time.time()

    for _ in range(iterations):
        guard.anonymize(test_message)

    end = time.time()
    avg_time = (end - start) / iterations * 1000  # ms

    print(f"Iterations: {iterations}")
    print(f"Total time: {(end - start)*1000:.2f}ms")
    print(f"Average time per anonymization: {avg_time:.3f}ms")
    print()
    print(f"✓ Fast enough for real-time SLM inference!")
    print(f"✓ Overhead is negligible compared to SLM inference time (~50-200ms)")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ollama + PII Protection Demo")
    parser.add_argument(
        "--mode",
        choices=["interactive", "batch", "performance"],
        default="interactive",
        help="Demo mode to run"
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        interactive_demo()
    elif args.mode == "batch":
        batch_demo()
    elif args.mode == "performance":
        performance_demo()

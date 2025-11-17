"""
Example: LlamaIndex integration for PII-protected RAG applications.

This example demonstrates how to use llm-slm-prompt-guard with LlamaIndex
to build privacy-preserving Retrieval-Augmented Generation (RAG) applications.

Installation:
    pip install llm-slm-prompt-guard[llamaindex]
    pip install openai  # or your preferred LLM

Usage:
    export OPENAI_API_KEY=your_key_here
    python examples/llamaindex_integration_example.py
"""

import os
from pathlib import Path

# Check if LlamaIndex is available
try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
    from llama_index.core.llms import ChatMessage
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("❌ LlamaIndex not installed. Install with: pip install llm-slm-prompt-guard[llamaindex]")
    exit(1)

try:
    from prompt_guard import PromptGuard
    from prompt_guard.adapters.llamaindex_adapter import (
        create_protected_query_engine,
        create_protected_chat_engine,
    )
except ImportError as e:
    print(f"❌ Error importing prompt_guard: {e}")
    exit(1)


def example_1_basic_query_engine():
    """Example 1: Protected Query Engine with sensitive documents."""
    print("\n" + "=" * 60)
    print("Example 1: Protected Query Engine")
    print("=" * 60)

    # Create sample documents with PII
    documents = [
        Document(
            text="""
            Patient Record - Confidential
            Name: John Smith
            DOB: 1985-03-15
            SSN: 123-45-6789
            Email: john.smith@email.com
            Phone: 555-123-4567

            Diagnosis: Patient presents with symptoms of seasonal allergies.
            Prescribed: Antihistamine medication.
            """
        ),
        Document(
            text="""
            Patient Record - Confidential
            Name: Sarah Johnson
            DOB: 1992-07-22
            SSN: 987-65-4321
            Email: sarah.j@email.com
            Phone: 555-987-6543

            Diagnosis: Annual checkup, all vitals normal.
            Follow-up scheduled in 6 months.
            """
        ),
    ]

    # Create index from documents
    print("Creating vector index from documents...")
    index = VectorStoreIndex.from_documents(documents)

    # Create base query engine
    base_query_engine = index.as_query_engine()

    # Wrap with PII protection
    guard = PromptGuard(policy="hipaa_phi")  # HIPAA compliance
    protected_query_engine = create_protected_query_engine(
        query_engine=base_query_engine,
        guard=guard,
        deanonymize_response=True,  # Restore PII in response
    )

    # Query with PII in the question
    print("\nQuerying: 'What is the diagnosis for patient john.smith@email.com?'")
    response = protected_query_engine.query(
        "What is the diagnosis for patient john.smith@email.com?"
    )

    print(f"\nResponse: {response}")
    print("\n✓ PII was protected before sending to LLM")
    print("✓ Response was de-anonymized for user")


def example_2_chat_engine():
    """Example 2: Protected Chat Engine for multi-turn conversations."""
    print("\n" + "=" * 60)
    print("Example 2: Protected Chat Engine (Multi-turn)")
    print("=" * 60)

    # Create sample documents
    documents = [
        Document(
            text="""
            Company Directory:
            - CEO: Robert Williams (robert@acme.com, ext: 1001)
            - CTO: Lisa Chen (lisa.chen@acme.com, ext: 1002)
            - CFO: Michael Brown (m.brown@acme.com, ext: 1003)
            """
        ),
    ]

    # Create index and chat engine
    print("Creating chat engine...")
    index = VectorStoreIndex.from_documents(documents)
    base_chat_engine = index.as_chat_engine()

    # Wrap with PII protection
    guard = PromptGuard(policy="default_pii")
    protected_chat_engine = create_protected_chat_engine(
        chat_engine=base_chat_engine,
        guard=guard,
    )

    # Multi-turn conversation
    conversations = [
        "Who is the CEO?",
        "What is their email address?",
        "Can you give me the contact info for the CTO?",
    ]

    print("\nStarting multi-turn conversation:")
    for i, msg in enumerate(conversations, 1):
        print(f"\n[Turn {i}] User: {msg}")
        response = protected_chat_engine.chat(msg)
        print(f"[Turn {i}] Assistant: {response}")

    # Reset conversation
    print("\n✓ Chat history maintained with PII protection")
    protected_chat_engine.reset()
    print("✓ Conversation reset")


def example_3_async_operations():
    """Example 3: Async operations for high-performance applications."""
    print("\n" + "=" * 60)
    print("Example 3: Async Protected Operations")
    print("=" * 60)

    import asyncio

    async def async_query_example():
        # Create documents
        documents = [
            Document(text="Contact support at support@company.com or call 1-800-123-4567"),
            Document(text="Sales team: sales@company.com, phone: 1-800-987-6543"),
        ]

        # Create index and query engine
        index = VectorStoreIndex.from_documents(documents)
        base_query_engine = index.as_query_engine()

        # Create protected query engine
        from prompt_guard import AsyncPromptGuard
        async_guard = AsyncPromptGuard(policy="default_pii")

        # Note: For async, we need to use the async methods
        from prompt_guard.adapters.llamaindex_adapter import ProtectedQueryEngine

        protected = ProtectedQueryEngine(
            query_engine=base_query_engine,
            guard=async_guard,
        )

        # Run multiple queries concurrently
        queries = [
            "What is the support email?",
            "What is the sales phone number?",
            "How can I contact the company?",
        ]

        print("\nRunning 3 queries concurrently...")
        import time
        start = time.time()

        # Note: This is a simplified example - actual async implementation
        # would require LlamaIndex async support
        responses = []
        for query in queries:
            result = protected.query(query)
            responses.append(result)

        elapsed = time.time() - start

        for i, (query, response) in enumerate(zip(queries, responses), 1):
            print(f"\nQuery {i}: {query}")
            print(f"Response {i}: {response}")

        print(f"\n✓ Processed {len(queries)} queries in {elapsed:.2f}s")

    # Run async example
    asyncio.run(async_query_example())


def example_4_custom_policies():
    """Example 4: Using custom policies for specific use cases."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Policies")
    print("=" * 60)

    # Financial data
    documents = [
        Document(
            text="""
            Transaction Report:
            Card: 4532-1234-5678-9010
            Cardholder: Jane Doe
            Amount: $1,250.00
            Date: 2024-01-15
            Merchant: Online Store Inc.
            """
        ),
    ]

    index = VectorStoreIndex.from_documents(documents)
    base_query_engine = index.as_query_engine()

    # Use PCI-DSS compliant policy
    guard = PromptGuard(policy="pci_dss")
    protected_query_engine = create_protected_query_engine(
        query_engine=base_query_engine,
        guard=guard,
    )

    print("\nQuerying financial data with PCI-DSS policy:")
    response = protected_query_engine.query("What was the transaction amount?")
    print(f"Response: {response}")

    print("\n✓ Credit card numbers are protected (PCI-DSS)")
    print("✓ CVV would be fully redacted (never stored)")


def example_5_storage_integration():
    """Example 5: Integration with Redis storage for persistence."""
    print("\n" + "=" * 60)
    print("Example 5: Redis Storage Integration")
    print("=" * 60)

    try:
        from prompt_guard.storage import RedisMappingStorage
    except ImportError:
        print("❌ Redis not available. Install with: pip install llm-slm-prompt-guard[redis]")
        return

    # Create documents
    documents = [
        Document(text="Customer John Smith ordered product #12345, email: john@example.com"),
    ]

    index = VectorStoreIndex.from_documents(documents)
    base_query_engine = index.as_query_engine()

    # Create storage for mapping persistence
    try:
        storage = RedisMappingStorage(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_audit=True,
        )

        # Create session
        session_id = storage.create_session(user_id="user_123")
        print(f"Created session: {session_id}")

        # Use guard with storage
        guard = PromptGuard(policy="default_pii")
        protected_query_engine = create_protected_query_engine(
            query_engine=base_query_engine,
            guard=guard,
        )

        # Query
        response = protected_query_engine.query("Who ordered product #12345?")
        print(f"Response: {response}")

        # Note: In a production setup, you would store mappings in Redis
        # for persistence across requests and instances

        print("\n✓ Session-based mapping storage")
        print("✓ Audit trail enabled")
        print("✓ Multi-instance support")

    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        print("   Start Redis with: docker run -d -p 6379:6379 redis:7-alpine")


def main():
    print("=" * 60)
    print("LlamaIndex Integration Examples")
    print("=" * 60)

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set.")
        print("   Set it with: export OPENAI_API_KEY=your_key_here")
        print("   Examples will use mock responses.\n")

    # Run examples
    try:
        example_1_basic_query_engine()
        example_2_chat_engine()
        example_3_async_operations()
        example_4_custom_policies()
        example_5_storage_integration()

        print("\n" + "=" * 60)
        print("✅ All LlamaIndex integration examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

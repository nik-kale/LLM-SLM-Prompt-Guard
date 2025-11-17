llm-slm-prompt-guard Documentation
====================================

Enterprise-grade PII anonymization and de-anonymization for Large Language Model (LLM)
and Small Language Model (SLM) applications.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   concepts

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/basic_usage
   user_guide/detectors
   user_guide/policies
   user_guide/caching
   user_guide/storage
   user_guide/async_operations
   user_guide/batch_processing

.. toctree::
   :maxdepth: 2
   :caption: Framework Integrations

   integrations/langchain
   integrations/llamaindex
   integrations/huggingface
   integrations/vercel_ai
   integrations/http_proxy

.. toctree::
   :maxdepth: 2
   :caption: Compliance

   compliance/hipaa
   compliance/pci_dss
   compliance/gdpr
   compliance/audit_logging

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   deployment/docker
   deployment/kubernetes
   deployment/monitoring
   deployment/scaling

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/core
   api/detectors
   api/adapters
   api/storage
   api/cache
   api/types

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/testing
   development/security
   development/benchmarks

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   roadmap
   faq
   examples

Overview
--------

**llm-slm-prompt-guard** is a production-ready library for protecting sensitive
information (PII) in LLM/SLM applications. It provides:

* 🔒 **Policy-driven PII detection** using regex and ML-based detectors
* 🔄 **Reversible anonymization** with de-anonymization support
* ⚡ **High-performance async/await** for scalable applications
* 🎯 **Industry compliance** (HIPAA, PCI-DSS, GDPR)
* 🔌 **Framework integrations** (LangChain, LlamaIndex, Hugging Face)
* 📊 **Audit logging** with PostgreSQL and Redis
* 🌐 **Multi-language support** (10+ languages)
* 🚀 **Zero-code HTTP proxy** for any LLM API

Quick Example
-------------

.. code-block:: python

   from prompt_guard import PromptGuard

   # Initialize with default PII policy
   guard = PromptGuard(policy="default_pii")

   # Anonymize text
   text = "Contact John at john@example.com or 555-123-4567"
   anonymized, mapping = guard.anonymize(text)

   # Output: "Contact [PERSON_1] at [EMAIL_1] or [PHONE_1]"
   print(anonymized)

   # De-anonymize response
   response = f"I will contact [PERSON_1] at [EMAIL_1]"
   original = guard.deanonymize(response, mapping)

   # Output: "I will contact John at john@example.com"
   print(original)

Key Features
------------

Core Functionality
~~~~~~~~~~~~~~~~~~

* **Detectors**: Regex, Enhanced Regex, Presidio (ML), spaCy (NER)
* **Policies**: Pre-built policies for HIPAA, PCI-DSS, GDPR, and custom policies
* **Caching**: In-memory and Redis-based distributed caching
* **Storage**: Redis and PostgreSQL for persistent mapping storage
* **Async Support**: Full async/await for high-concurrency applications

Framework Integrations
~~~~~~~~~~~~~~~~~~~~~

* **LangChain**: Protect LLM chains and agents
* **LlamaIndex**: Secure RAG applications
* **Hugging Face**: Protect transformers pipelines
* **Vercel AI SDK**: Streaming chat protection
* **HTTP Proxy**: Zero-code integration for any LLM API

Enterprise Features
~~~~~~~~~~~~~~~~~~

* **Compliance**: HIPAA/PHI, PCI-DSS, GDPR policies
* **Audit Logging**: PostgreSQL-based audit trail
* **Monitoring**: Prometheus metrics and Grafana dashboards
* **Deployment**: Docker, Kubernetes, auto-scaling
* **Security**: Input validation, ReDoS protection, data leakage prevention

Performance
-----------

* **Regex Detection**: <1ms latency, 10,000+ req/s
* **ML Detection**: 10ms latency, 1,000+ req/s
* **With Cache**: <0.1ms latency, 50,000+ req/s
* **HTTP Proxy**: 15ms latency, 500+ req/s

Installation
------------

.. code-block:: bash

   # Basic installation
   pip install llm-slm-prompt-guard

   # With ML detectors
   pip install llm-slm-prompt-guard[presidio,spacy]

   # With framework integrations
   pip install llm-slm-prompt-guard[langchain,llamaindex]

   # With storage backends
   pip install llm-slm-prompt-guard[redis,postgres]

   # Full installation
   pip install llm-slm-prompt-guard[all]

Support
-------

* **GitHub**: https://github.com/nik-kale/llm-slm-prompt-guard
* **Issues**: https://github.com/nik-kale/llm-slm-prompt-guard/issues
* **Discussions**: https://github.com/nik-kale/llm-slm-prompt-guard/discussions

License
-------

MIT License - see LICENSE file for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

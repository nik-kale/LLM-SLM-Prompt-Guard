Detectors API
=============

This section documents all available PII detectors.

Base Detector
-------------

.. autoclass:: prompt_guard.detectors.BaseDetector
   :members:
   :undoc-members:
   :show-inheritance:

Regex Detector
--------------

Basic regex-based PII detector.

.. autoclass:: prompt_guard.detectors.RegexDetector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Enhanced Regex Detector
-----------------------

Advanced regex detector with international support.

.. autoclass:: prompt_guard.detectors.EnhancedRegexDetector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Presidio Detector
-----------------

ML-based detector using Microsoft Presidio.

.. autoclass:: prompt_guard.detectors.PresidioDetector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

spaCy Detector
--------------

ML-based detector using spaCy NER.

.. autoclass:: prompt_guard.detectors.SpacyDetector
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

import os
import sys

# The proxy is run as a script from packages/proxy/src, so its modules are
# imported by file name (``main``, ``rate_limiter``).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

"""TLS trust configuration for corporate networks.

Behind a TLS-inspecting proxy, the certifi bundle the Anthropic/Google SDKs ship
with does not contain the proxy's signing CA, so an LLM call fails with
CERTIFICATE_VERIFY_FAILED even though the browser on the same machine is fine.
`truststore` makes Python validate against the OS trust store instead, where the
corporate CA already lives.

Called from the entry points (CLI, API, smoke script) rather than at import, so
importing the library never mutates global SSL behaviour.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_APPLIED = False


def enable_system_trust_store() -> bool:
    """Route TLS verification through the OS trust store. Returns True if applied.

    Set `TAXPILOT_DISABLE_TRUSTSTORE=1` to skip it, e.g. to point `SSL_CERT_FILE`
    at an explicit CA bundle yourself.
    """
    global _APPLIED
    if _APPLIED or os.environ.get("TAXPILOT_DISABLE_TRUSTSTORE") == "1":
        return _APPLIED

    try:
        import truststore
    except ImportError:
        logger.debug("truststore not installed - using the default certifi bundle")
        return False

    truststore.inject_into_ssl()
    _APPLIED = True
    logger.info("TLS verification is using the system trust store")
    return True

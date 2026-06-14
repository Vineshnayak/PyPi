import re
from faultsnap.config import config

def is_sensitive_key(key: str) -> bool:
    """Check if a dictionary key or variable name matches sensitive patterns."""
    if not isinstance(key, str):
        return False
    return any(pattern.match(key) for pattern in config._compiled_patterns)

def mask_value(value: str) -> str:
    """Return a masked placeholder."""
    return "********"

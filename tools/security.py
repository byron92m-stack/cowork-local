"""Security module for Cowork-Local."""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"system\s*prompt\s*:",
    r"you\s+are\s+now\s+DAN",
    r"pretend\s+you\s+are",
    r"new\s+instructions?\s*:",
]

def detect_injection(user_input: str) -> Optional[str]:
    """Detect prompt injection attempts."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(f"Possible injection detected: {pattern}")
            return f"Security: Input blocked"
    return None

def sanitize_input(user_input: str) -> str:
    """Sanitize user input."""
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', user_input)
    return sanitized[:10000] if len(sanitized) > 10000 else sanitized

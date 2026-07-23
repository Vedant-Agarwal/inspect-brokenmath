"""Helpers for generating stable, collision-resistant sample IDs."""

from __future__ import annotations

import hashlib
from typing import Any


def create_stable_id(*fields: Any, prefix: str = "", length: int = 8) -> str:
    """Create a stable, deterministic ID from one or more content fields.

    Useful for datasets without a natural ID field, especially when the order
    is shuffled — hashing stable content keeps a sample's ID consistent across
    shuffles and reruns.

    Args:
        *fields: One or more fields to hash (e.g. question text, passage,
            other unique content).
        prefix: Optional dataset/eval prefix (e.g. ``"boolq"``) prepended to
            the hash with an underscore. Empty by default.
        length: Number of hex characters from the hash to keep. Default 8.

    Returns:
        A stable ID like ``"boolq_a4f3d9e2"`` (with prefix) or ``"a4f3d9e2"``.

    Example:
        >>> create_stable_id("What is the capital of France?", prefix="boolq")
        'boolq_a4f3d9e2'
    """
    # Null-byte delimiter prevents collisions like ("ab", "c") vs ("a", "bc").
    combined = "\0".join(str(field) for field in fields)
    hash_value = hashlib.md5(combined.encode()).hexdigest()[:length]
    return f"{prefix}_{hash_value}" if prefix else hash_value

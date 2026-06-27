"""Prefixed, URL-safe, opaque IDs. See docs/api/README.md."""
from __future__ import annotations

import secrets


def gen_id(prefix: str, n_hex: int = 12) -> str:
    """e.g. gen_id("pet") -> "pet_2b7d4f10a6c1"."""
    return f"{prefix}_{secrets.token_hex(n_hex // 2)}"

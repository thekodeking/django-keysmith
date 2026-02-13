from __future__ import annotations

import secrets
import string
import zlib
from dataclasses import dataclass

from keysmith.settings import keysmith_settings

_DICTIONARY = string.ascii_letters + string.digits


@dataclass(frozen=True)
class PublicToken:
    """
    Immutable representation of a generated public token and
    its non-sensitive derived components.
    """

    token: str
    full_prefix: str
    crc: str
    hint: str


def generate_raw_secret(length: int = 32) -> str:
    return "".join(secrets.choice(_DICTIONARY) for _ in range(length))


def compute_crc(value: str, crc_digits: int = 6) -> str:
    crc = (
        zlib.crc32(value.encode("utf-8")) & 0xFFFFFFFF
    )  # bitwise shennanigans to convert to unsigned int just to be safe
    mod = 10**crc_digits
    return f"{crc % mod:0{crc_digits}d}"


def build_public_token(
    *,
    namespace: str,
    identifier: str,
    secret: str,
) -> PublicToken:
    """Build the externally visible token plus derived, non-sensitive metadata."""
    full_prefix = f"{namespace}_{identifier}"
    body = f"{full_prefix}:{secret}"
    crc = compute_crc(body)

    public = f"{body}{crc}"
    hint = build_hint(crc=crc)

    return PublicToken(
        token=public,
        full_prefix=full_prefix,
        crc=crc,
        hint=hint,
    )


def extract_prefix_and_secret(public_token: str) -> tuple[str, str]:
    """Validate a public token and return `(prefix, secret)`."""
    if not public_token:
        raise ValueError("Token is empty")

    crc_len: int = 6

    if len(public_token) <= crc_len + 3:
        # must at least fit the format <p>_<id>:<s><crc>
        raise ValueError("Token too short")

    body = public_token[:-crc_len]
    provided_crc = public_token[-crc_len:]
    expected_crc = compute_crc(body)

    if not secrets.compare_digest(provided_crc, expected_crc):
        raise ValueError("Invalid token checksum")

    if ":" not in body:
        raise ValueError("Invalid token format")

    prefix_and_id, secret = body.split(":", 1)

    if "_" not in prefix_and_id:
        raise ValueError("Invalid token prefix format")

    if not secret:
        raise ValueError("Missing token secret")

    return prefix_and_id, secret


def build_hint(*, crc: str) -> str:
    """
    Build a short, non-sensitive hint that does not repeat prefix/token id.

    Format:
        h_<last N crc digits>

    Length is bounded by KEYSMITH["HINT_LENGTH"] and model constraints.
    """
    if not crc:
        return ""

    max_len = max(2, int(getattr(keysmith_settings, "HINT_LENGTH", 8) or 8))
    marker = "h_"
    tail_len = max(1, max_len - len(marker))
    return f"{marker}{crc[-tail_len:]}"

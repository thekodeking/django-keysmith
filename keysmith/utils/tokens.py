from __future__ import annotations

import secrets
import string
import zlib
from dataclasses import dataclass

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
    full_prefix = f"{namespace}_{identifier}"
    body = f"{full_prefix}:{secret}"
    crc = compute_crc(body)

    public = f"{body}{crc}"
    hint = build_hint(full_prefix=full_prefix, crc=crc)

    return PublicToken(
        token=public,
        full_prefix=full_prefix,
        crc=crc,
        hint=hint,
    )


def extract_prefix_and_secret(public_token: str) -> tuple[str, str]:
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


def build_hint(*, full_prefix: str, crc: str) -> str:
    """
    Build a non-sensitive human-readable hint.

    Format:
        <prefix>_<id>…<last N crc digits>
    """
    if not full_prefix or not crc:
        return ""

    crc_length: int = 6
    crc_tail_len = max(1, crc_length // 2)
    return f"{full_prefix}…{crc[-crc_tail_len:]}"

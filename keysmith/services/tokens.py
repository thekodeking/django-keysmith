from __future__ import annotations

from datetime import timedelta
from typing import Iterable, Tuple

from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string
from keysmith.hashers.registry import get_hasher
from keysmith.models import Token
from keysmith.settings import keysmith_settings
from keysmith.utils.tokens import (
    PublicToken,
    generate_raw_secret,
    build_public_token,
    build_hint,
)
from keysmith.hashers.base import BaseTokenHasher


def _default_expiry():
    if keysmith_settings.DEFAULT_EXPIRY_DAYS:
        return timezone.now() + timedelta(days=keysmith_settings.DEFAULT_EXPIRY_DAYS)
    return None


def _generate_unique_prefix() -> str:
    base = keysmith_settings.TOKEN_PREFIX
    length = 8

    for _ in range(5):
        token_id = generate_raw_secret(length)
        prefix = f"{base}_{token_id}"

        if not Token.objects.filter(prefix=prefix).exists():
            return prefix

    raise RuntimeError("Failed to generate unique token prefix")


@transaction.atomic
def create_token(
    *,
    name: str,
    description: str = "",
    created_by=None,
    user=None,
    scopes: Iterable = None,
    expires_at=None,
    token_type: str = Token.TokenType.USER,
) -> Tuple[Token, str]:
    hasher: BaseTokenHasher = get_hasher()
    secret: str = generate_raw_secret()
    full_prefix: str = _generate_unique_prefix()

    namespace, identifier = full_prefix.rsplit("_", 1)
    pt: PublicToken = build_public_token(
        secret=secret,
        identifier=identifier,
        namespace=namespace,
    )
    hashed: str = hasher.hash(secret)

    token = Token.objects.create(
        name=name,
        description=description,
        created_by=created_by,
        user=user,
        token_type=token_type,
        key=hashed,
        prefix=pt.full_prefix,
        hint=pt.hint,
        expires_at=expires_at or _default_expiry(),
    )

    if scopes is not None:
        token.scopes.set(scopes)

    return token, pt.token


@transaction.atomic
def rotate_token(token: Token) -> str:
    if token.revoked or token.purged:
        raise ValueError("Cannot rotate a revoked or purged token")

    hasher: BaseTokenHasher = get_hasher()
    secret: str = generate_raw_secret(keysmith_settings.TOKEN_LENGTH)
    namespace, identifier = token.prefix.rsplit("_", 1)

    pt: PublicToken = build_public_token(
        secret=secret,
        identifier=identifier,
        namespace=namespace,
    )

    token.key = hasher.hash(secret)
    token.hint = pt.hint
    token.last_used_at = None
    token.save(update_fields=["key", "hint", "last_used_at"])

    return pt.token


@transaction.atomic
def revoke_token(token: Token, *, purge: bool = False) -> None:
    updates = {}

    if not token.revoked:
        updates["revoked"] = True

    if purge and not token.purged:
        updates["purged"] = True

    if updates:
        token.__class__.objects.filter(pk=token.pk).update(**updates)


def mark_token_used(token: Token) -> None:
    Token.objects.filter(pk=token.pk).update(last_used_at=timezone.now())

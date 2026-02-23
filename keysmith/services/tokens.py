from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from keysmith.audit.logger import log_audit_event
from keysmith.hashers.base import BaseTokenHasher
from keysmith.hashers.registry import get_hasher
from keysmith.models.utils import get_token_model
from keysmith.settings import keysmith_settings
from keysmith.utils.tokens import (
    PublicToken,
    build_public_token,
    generate_raw_secret,
)


def _default_expiry():
    if keysmith_settings.DEFAULT_EXPIRY_DAYS:
        return timezone.now() + timedelta(days=keysmith_settings.DEFAULT_EXPIRY_DAYS)
    return None


def _generate_unique_prefix() -> str:
    Token = get_token_model()
    base = keysmith_settings.TOKEN_PREFIX
    length = 8

    for _ in range(5):
        token_id = generate_raw_secret(length)
        prefix = f"{base}_{token_id}"

        if not Token.objects.filter(prefix=prefix).exists():
            return prefix

    raise RuntimeError("Failed to generate unique token prefix")


def _validate_available_scopes(scope_codenames: set[str]) -> None:
    available = set(keysmith_settings.AVAILABLE_SCOPES or [])
    if not available or not scope_codenames:
        return

    disallowed = scope_codenames - available
    if disallowed:
        disallowed_values = ", ".join(sorted(disallowed))
        raise ValueError(
            f"Requested scopes are not in AVAILABLE_SCOPES: {disallowed_values}"
        )


def _extract_scope_codenames(scopes: Iterable) -> set[str]:
    if hasattr(scopes, "values_list"):
        return set(scopes.values_list("codename", flat=True))

    codenames = set()
    for scope in scopes:
        codename = getattr(scope, "codename", None)
        if not codename:
            raise TypeError(
                "Scopes must be Permission instances (or a queryset of Permission instances)."
            )
        codenames.add(codename)
    return codenames


def _resolve_permissions_by_codename(scope_codenames: set[str]):
    from django.contrib.auth.models import Permission

    if not scope_codenames:
        return Permission.objects.none()

    permissions = Permission.objects.filter(codename__in=scope_codenames)
    found = set(permissions.values_list("codename", flat=True))
    missing = scope_codenames - found
    if missing:
        missing_values = ", ".join(sorted(missing))
        raise ValueError(f"Scope permissions were not found: {missing_values}")
    return permissions


@transaction.atomic
def create_token(
    *,
    name: str,
    description: str = "",
    created_by=None,
    user=None,
    scopes: Iterable = None,
    expires_at=None,
    token_type: str | None = None,
):
    """Create and persist a new token, returning `(token, raw_public_token)`."""
    Token = get_token_model()
    max_name_length = Token._meta.get_field("name").max_length
    if max_name_length is not None and len(name) > max_name_length:
        raise ValueError(
            f"Token name must be {max_name_length} characters or fewer (got {len(name)})."
        )

    if token_type is None:
        token_type = Token.TokenType.USER
    hasher: BaseTokenHasher = get_hasher()
    secret: str = generate_raw_secret(keysmith_settings.TOKEN_SECRET_LENGTH)
    full_prefix: str = _generate_unique_prefix()

    namespace, identifier = full_prefix.rsplit("_", 1)
    pt: PublicToken = build_public_token(
        secret=secret,
        identifier=identifier,
        namespace=namespace,
    )
    hashed: str = hasher.hash(secret)

    scopes_to_assign = scopes
    if scopes_to_assign is None:
        default_scope_codenames = set(keysmith_settings.DEFAULT_SCOPES or [])
        _validate_available_scopes(default_scope_codenames)
        scopes_to_assign = _resolve_permissions_by_codename(default_scope_codenames)
    else:
        if not hasattr(scopes_to_assign, "values_list"):
            scopes_to_assign = list(scopes_to_assign)
        requested_scope_codenames = _extract_scope_codenames(scopes_to_assign)
        _validate_available_scopes(requested_scope_codenames)

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

    if scopes_to_assign is not None:
        token.scopes.set(scopes_to_assign)

    return token, pt.token


@transaction.atomic
def rotate_token(token, *, request=None, actor=None) -> str:
    """Rotate a token secret/hash and emit an audit entry."""
    if token.revoked or token.purged:
        raise ValueError("Cannot rotate a revoked or purged token")

    hasher: BaseTokenHasher = get_hasher()
    secret: str = generate_raw_secret(keysmith_settings.TOKEN_SECRET_LENGTH)
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
    log_audit_event(
        action="rotated",
        request=request,
        token=token,
        status_code=200,
        extra={"actor_id": getattr(actor, "pk", None)},
    )

    return pt.token


@transaction.atomic
def revoke_token(token, *, purge: bool = False, request=None, actor=None) -> None:
    """Revoke (and optionally purge) a token and log the lifecycle event."""
    updates = {}

    if not token.revoked:
        updates["revoked"] = True

    if purge and not token.purged:
        updates["purged"] = True

    if updates:
        token.__class__.objects.filter(pk=token.pk).update(**updates)
        for field, value in updates.items():
            setattr(token, field, value)
        log_audit_event(
            action="revoked",
            request=request,
            token=token,
            status_code=200,
            extra={
                "actor_id": getattr(actor, "pk", None),
                "purge": purge,
            },
        )


def mark_token_used(token) -> None:
    token.__class__.objects.filter(pk=token.pk).update(last_used_at=timezone.now())

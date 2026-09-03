from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from django.db import IntegrityError, transaction
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
        raise ValueError(f"Requested scopes are not in AVAILABLE_SCOPES: {disallowed_values}")


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
    from django.db.models import Q

    if not scope_codenames:
        return Permission.objects.none()

    q_filter = Q()
    for scope in scope_codenames:
        if "." in scope:
            app_label, codename = scope.split(".", 1)
            q_filter |= Q(content_type__app_label=app_label, codename=codename)
        else:
            q_filter |= Q(codename=scope)

    permissions = Permission.objects.filter(q_filter).select_related("content_type")

    found_scopes = set()
    for p in permissions:
        found_scopes.add(f"{p.content_type.app_label}.{p.codename}")
        found_scopes.add(p.codename)

    missing = scope_codenames - found_scopes
    if missing:
        missing_values = ", ".join(sorted(missing))
        raise ValueError(f"Scope permissions were not found: {missing_values}")
    return permissions


def create_token(
    *,
    name: str,
    description: str = "",
    created_by=None,
    user=None,
    scopes: Iterable = None,
    expires_at=None,
    token_type: str | None = None,
    request=None,
):
    """Create and persist a new token, returning `(token, raw_public_token)`.

    Passing ``request`` is optional; when provided the audit event will
    include request context (path, IP, user-agent).
    """
    Token = get_token_model()
    max_name_length = Token._meta.get_field("name").max_length
    if max_name_length is not None and len(name) > max_name_length:
        raise ValueError(
            f"Token name must be {max_name_length} characters or fewer (got {len(name)})."
        )
    if token_type is None:
        token_type = Token.TokenType.USER
    hasher: BaseTokenHasher = get_hasher()

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

    for attempt in range(5):
        secret: str = generate_raw_secret(keysmith_settings.TOKEN_SECRET_LENGTH)
        full_prefix: str = _generate_unique_prefix()

        namespace, identifier = full_prefix.rsplit("_", 1)
        pt: PublicToken = build_public_token(
            secret=secret,
            identifier=identifier,
            namespace=namespace,
        )
        hashed: str = hasher.hash(secret)

        try:
            with transaction.atomic():
                token = Token.objects.create(
                    name=name,
                    description=description,
                    created_by=created_by,
                    user=user,
                    token_type=token_type,
                    key=hashed,
                    prefix=pt.full_prefix,
                    expires_at=expires_at or _default_expiry(),
                )

                if scopes_to_assign is not None:
                    token.scopes.set(scopes_to_assign)
        except IntegrityError:
            if attempt == 4:
                raise
            continue
        break
    else:
        raise RuntimeError("Failed to generate unique token prefix")

    log_audit_event(
        action="created",
        request=request,
        token=token,
        status_code=201,
        extra={
            "actor_id": getattr(created_by or user, "pk", None),
            "token_name": name,
        },
    )

    return token, pt.token


@transaction.atomic
def rotate_token(token, *, expires_at=None, request=None, actor=None) -> str:
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

    update_fields = ["key", "last_used_at"]
    token.key = hasher.hash(secret)
    token.last_used_at = None

    if expires_at is not None:
        token.expires_at = expires_at
        update_fields.append("expires_at")
    elif token.is_expired:
        token.expires_at = _default_expiry()
        update_fields.append("expires_at")

    token.save(update_fields=update_fields)
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
    """Revoke a token and log the lifecycle event.

    When ``purge=True`` this delegates to :func:`purge_token` for compatibility.
    """
    if purge:
        purge_token(token, request=request, actor=actor)
        return

    if token.revoked:
        return

    token.__class__.objects.filter(pk=token.pk).update(revoked=True)
    token.revoked = True
    log_audit_event(
        action="revoked",
        request=request,
        token=token,
        status_code=200,
        extra={
            "actor_id": getattr(actor, "pk", None),
            "purge": False,
        },
    )


@transaction.atomic
def purge_token(token, *, request=None, actor=None) -> None:
    """Soft-delete a token by marking it purged (and revoked)."""
    updates = {}
    if not token.revoked:
        updates["revoked"] = True
    if not token.purged:
        updates["purged"] = True

    if not updates:
        return

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
            "purge": True,
        },
    )


def mark_token_used(token) -> None:
    now = timezone.now()
    interval = getattr(keysmith_settings, "LAST_USED_UPDATE_INTERVAL", 60)
    if (
        interval > 0
        and token.last_used_at is not None
        and (now - token.last_used_at).total_seconds() < interval
    ):
        return

    updated = (
        token.__class__.objects.filter(pk=token.pk, revoked=False, purged=False)
        .update(last_used_at=now)
    )
    if updated or token.last_used_at is None:
        token.last_used_at = now

# Services API

Service functions live in `keysmith.services.tokens` unless noted. These APIs are the recommended path for token lifecycle operations because they enforce consistency and emit audit events where expected.

## `create_token(...)`

`create_token` is the canonical entry point for issuing new credentials.

```python
create_token(
    *,
    name: str,
    description: str = "",
    created_by=None,
    user=None,
    scopes: Iterable = None,
    expires_at=None,
    token_type: str | None = None,
)
```

Creates and persists a token, returns `(token, raw_public_token)`.

Important behavior:

- Generates a unique prefixed identifier.
- Builds public token string with checksum.
- Hashes secret before persistence.
- Applies `DEFAULT_SCOPES` when explicit `scopes` is omitted.
- Enforces `AVAILABLE_SCOPES` when configured.

## `rotate_token(token, *, request=None, actor=None) -> str`

Use rotation to replace compromised or aging credentials while retaining token identity.

Replaces token secret/hash and returns a new raw token.

- Clears `last_used_at`
- Logs `rotated` event
- Raises `ValueError` if token is revoked or purged

## `revoke_token(token, *, purge=False, request=None, actor=None) -> None`

Revocation is terminal for authentication and should be the default response for decommissioned credentials.

Marks token revoked.

- Logs `revoked` event when state changes
- Includes `actor_id` and `purge=False` metadata in audit `extra`

`purge=True` remains supported for backward compatibility and delegates to `purge_token(...)`.

## `purge_token(token, *, request=None, actor=None) -> None`

Purge is a soft-delete operation that marks a token as permanently retired.

- Marks both `purged=True` and `revoked=True`
- Logs `revoked` event with `purge=True` metadata in audit `extra`

## `mark_token_used(token) -> None`

This helper updates usage timestamps and is called automatically by successful authentication.

Updates `last_used_at` to current time.

## `authenticate_token(raw_token: str)`

Source: `keysmith.auth.base`

Returns the authenticated token instance or raises:

- `InvalidToken`
- `ExpiredToken`
- `RevokedToken`

This function performs parsing, lookup, lifecycle checks, hash verify, and usage timestamp updates in a single transaction.

## `log_audit_event(...)`

Source: `keysmith.audit.logger`

```python
log_audit_event(
    *,
    action: str,
    request=None,
    token=None,
    status_code: int = 0,
    extra: dict | None = None,
) -> None
```

No-op when `ENABLE_AUDIT_LOGGING=False`.
Failures are swallowed to avoid blocking authentication flow.

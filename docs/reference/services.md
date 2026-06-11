# Services

Module: `keysmith.services.tokens`

These are the canonical APIs for token lifecycle. Prefer them over direct model manipulation.

---

## `create_token`

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
    request=None,
) -> tuple[Token, str]
```

Creates a token and returns `(token, raw_public_token)`.

- Generates unique prefix and secret
- Hashes secret before persistence
- Validates name length and scopes against `AVAILABLE_SCOPES`
- Applies `DEFAULT_SCOPES` when `scopes` is `None`
- Logs `created` audit event
- Retries up to 5 times on `IntegrityError` (prefix collision)

**Raises:** `ValueError` for invalid name, scopes, or missing permissions. `RuntimeError` if prefix generation fails.

---

## `rotate_token`

```python
rotate_token(token, *, request=None, actor=None) -> str
```

Replaces secret hash. Returns new raw token. Clears `last_used_at`. Logs `rotated`.

**Raises:** `ValueError` if token is revoked or purged.

---

## `revoke_token`

```python
revoke_token(token, *, purge: bool = False, request=None, actor=None) -> None
```

Sets `revoked=True`. Idempotent. Logs `revoked` with `extra.purge=False`.

`purge=True` delegates to `purge_token()`.

---

## `purge_token`

```python
purge_token(token, *, request=None, actor=None) -> None
```

Sets `purged=True` and `revoked=True`. Idempotent. Logs `revoked` with `extra.purge=True`.

---

## `mark_token_used`

```python
mark_token_used(token) -> None
```

Updates `last_used_at`. Called automatically by `authenticate_token()`.

---

## `authenticate_token`

Module: `keysmith.auth.base`

```python
authenticate_token(raw_token: str) -> Token
```

Full validation pipeline inside a transaction.

**Raises:**

```python
keysmith.auth.exceptions.InvalidToken
keysmith.auth.exceptions.ExpiredToken
keysmith.auth.exceptions.RevokedToken
```

---

## `log_audit_event`

Module: `keysmith.audit.logger`

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

No-op when `ENABLE_AUDIT_LOGGING=False`. Uses `AUDIT_LOG_HOOK` when configured. Swallows all exceptions.

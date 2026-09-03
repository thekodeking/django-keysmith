# Services API Reference

Module: `keysmith.services.tokens` and `keysmith.auth.base`

These functions constitute Keysmith's core Python programmatic API. Always prefer these service functions over modifying `Token` model instances directly, as they handle prefix generation, constant-time hashing, scope validation, and audit event logging.

---

## `create_token`

Issue a new API token, hash its secret, persist it to the database, and return the token instance along with the raw one-time credential string.

```python
from keysmith.services.tokens import create_token

token, raw_token = create_token(
    *,
    name: str,
    description: str = "",
    created_by: Any = None,
    user: Any = None,
    scopes: Iterable = None,
    expires_at: datetime | None = None,
    token_type: str | None = None,
    request: HttpRequest | None = None,
) -> tuple[Token, str]
```

### Parameters

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `name` | `str` | **Required** | Human-readable label for the token (max 128 characters). |
| `description` | `str` | `""` | Free-text description of the token's purpose. |
| `created_by` | `User | None` | `None` | The administrative user who authorized or created the token. |
| `user` | `User | None` | `None` | The Django user account linked to this token. If `None` and `token_type` is not specified, creates a system token. |
| `scopes` | `Iterable` | `None` | List of `Permission` instances or string codenames (e.g. `["orders.view_order"]`). If `None`, defaults to `DEFAULT_SCOPES`. |
| `expires_at` | `datetime | None` | `None` | Explicit expiration timestamp in UTC. If `None`, defaults to `now + DEFAULT_EXPIRY_DAYS`. |
| `token_type` | `str | None` | `None` | Either `"user"` or `"system"`. Inferred automatically if omitted. |
| `request` | `HttpRequest | None` | `None` | Optional incoming request object used to enrich audit logging with IP and User-Agent. |

### Returns
- `tuple[Token, str]`: A tuple containing the saved `Token` database instance and the one-time `raw_token` string (e.g. `tok_...:...`).

### Raises
- `ValueError`: If `name` exceeds 128 characters, or if requested scopes are not allowed under `AVAILABLE_SCOPES`.
- `RuntimeError`: If prefix collision resolution fails after 5 retries.

---

## `rotate_token`

Rotate a token's secret credential while preserving its prefix, metadata, and scopes.

```python
from keysmith.services.tokens import rotate_token

new_raw_token = rotate_token(
    token: Token,
    *,
    expires_at: datetime | None = None,
    request: HttpRequest | None = None,
    actor: Any = None,
) -> str
```

### Parameters

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `token` | `Token` | **Required** | The `Token` instance to rotate. |
| `expires_at` | `datetime | None` | `None` | Optional new expiration timestamp. If the token was previously expired, automatically renews with default expiry if not provided. |
| `request` | `HttpRequest | None` | `None` | Optional request object for audit logging. |
| `actor` | `User | None` | `None` | The user performing the rotation. |

### Returns
- `str`: The newly generated raw token string. The previous secret is immediately invalidated.

### Raises
- `ValueError`: If the token is revoked or purged.

---

## `revoke_token`

Deactivate a token by marking `revoked = True`. The token can no longer be used to authenticate requests.

```python
from keysmith.services.tokens import revoke_token

revoke_token(
    token: Token,
    *,
    purge: bool = False,
    request: HttpRequest | None = None,
    actor: Any = None,
) -> None
```

### Parameters

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `token` | `Token` | **Required** | The `Token` instance to revoke. |
| `purge` | `bool` | `False` | When `True`, delegates to `purge_token()`. |
| `request` | `HttpRequest | None` | `None` | Optional request for audit logging. |
| `actor` | `User | None` | `None` | The user who requested revocation. |

---

## `purge_token`

Permanently soft-delete a token, marking both `purged = True` and `revoked = True`.

```python
from keysmith.services.tokens import purge_token

purge_token(
    token: Token,
    *,
    request: HttpRequest | None = None,
    actor: Any = None,
) -> None
```

---

## `authenticate_token`

Validate a raw token string, verify checksum, query database, and perform constant-time hash verification.

```python
from keysmith.auth.base import authenticate_token

token = authenticate_token(raw_token: str) -> Token
```

### Parameters

| Parameter | Type | Description |
| :--- | :---: | :--- |
| `raw_token` | `str` | The incoming credential string (e.g. `tok_...:...`). |

### Returns
- `Token`: The verified `Token` instance with linked user and scopes pre-fetched.

### Raises
- `InvalidToken`: If format or checksum is malformed, or prefix does not exist in the database, or hash comparison fails.
- `ExpiredToken`: If `token.expires_at < timezone.now()`.
- `RevokedToken`: If `token.revoked == True` or `token.purged == True`.

# Admin

Keysmith registers `Token` and `TokenAuditLog` in Django admin. Lifecycle operations in admin call the same service functions as your application code, so behavior and audit trails stay consistent.

---

## Token admin

### Creating a token

1. Go to **Tokens → Add token**
2. Fill in name, optional description, user, scopes, and expiry
3. Save - you are redirected to a one-time page showing the raw token
4. Copy the raw token immediately; it cannot be retrieved later

The admin `save_model` calls `create_token()` under the hood. The raw secret is stored briefly in the session and displayed once via the `token-created` view.

### Managing existing tokens

| Action | How |
| --- | --- |
| **Rotate** | Per-token "Rotate Token" button, or bulk action |
| **Revoke** | Bulk action on selected tokens |
| **Purge** | Bulk action on selected tokens |

Rotate is unavailable for tokens that are already revoked or purged.

### List view columns

ID, name, token type, prefix, user, revoked, purged, expires at, last used, created at.

Search by name, prefix, or user username/email. Filter by type, revoked/purged status, and dates.

---

## Audit log admin

Read-only. No create or edit.

| Column | Content |
| --- | --- |
| Action | `auth_success`, `auth_failed`, `created`, `rotated`, `revoked` |
| Token | Related token (if any) |
| Method, path | Request details |
| Status code | HTTP response |
| IP address | Client IP |
| Created at | Timestamp (date hierarchy enabled) |

Search by path, IP, user agent, or token prefix.

---

## Swappable models in admin

If you configure custom models via `TOKEN_MODEL` and `AUDIT_LOG_MODEL`, admin automatically uses them - provided they satisfy the [model contract](../reference/models.md#swappable-models).

---

**See also:** [Tokens](tokens.md) · [Audit logs](audit.md)

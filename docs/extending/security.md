# Security

What Keysmith guarantees, what it leaves to you, and how to deploy it safely.

---

## Guarantees

| Guarantee | Mechanism |
| --- | --- |
| No plaintext secrets | PBKDF2-SHA512 hash stored in `token.key` |
| Fast rejection of garbage | 6-digit CRC before database lookup |
| Lifecycle enforcement | Revoked, purged, and expired tokens blocked |
| Consistent validation | Single `authenticate_token()` for all integrations |
| Atomic operations | Transactions + `select_for_update` on auth and lifecycle |

---

## Your responsibilities

| Area | Recommendation |
| --- | --- |
| Transport | HTTPS everywhere in production |
| Distribution | Deliver raw tokens through secure channels |
| Storage (client side) | Treat raw tokens like passwords |
| Rate limiting | Wire `RATE_LIMIT_HOOK` / `DRF_THROTTLE_HOOK` |
| Database | Prefer PostgreSQL over SQLite for concurrent auth |

Keysmith warns (`keysmith.W001`) when SQLite is the default database because `SELECT FOR UPDATE` behavior differs under concurrency.

---

## Error disclosure {#error-disclosure}

Keysmith distinguishes failure reasons internally:

```text
TokenAuthError
├── InvalidToken
├── ExpiredToken
└── RevokedToken
```

**Do not expose these distinctions to API clients.** Telling an attacker whether a token exists, is expired, or is revoked leaks information about your credential store.

Keysmith maps all validation failures to one external message:

| Integration | Behavior |
| --- | --- |
| DRF | `AuthenticationFailed(get_message("invalid_token"))` |
| Django decorator | `HttpResponseUnauthorized` with `invalid_token` message |
| Custom code | Catch specific exceptions for internal logs; return generic 401 |

---

## Scope security

- Use `AVAILABLE_SCOPES` to prevent over-permissioning at creation
- Issue one token per integration boundary
- Set finite `DEFAULT_EXPIRY_DAYS`
- Rotate immediately after suspected exposure

---

## Audit integrity

Audit write failures are swallowed so auth never fails because logging is down. For compliance-critical environments, use `AUDIT_LOG_HOOK` to send events to a durable external system (SIEM, log aggregator) in addition to or instead of the database.

---

## Reporting vulnerabilities

Report security issues privately as described in [SECURITY.md](https://github.com/thekodeking/django-keysmith/blob/main/SECURITY.md).

---

**See also:** [Settings](../topics/settings.md) · [Audit logs](../topics/audit.md)

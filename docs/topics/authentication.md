# Authentication Pipeline & Performance

Learn how Keysmith processes credentials, prevents timing attacks, and minimizes database load.

---

## The Authentication Pipeline

When an API request arrives, Keysmith executes a high-speed, non-locking authentication sequence:

```text
Request arrives with Authorization header
                  │
                  ▼
         [ 1. Extract Token ]
  Extracts from Authorization: Bearer <token>
  or configured custom header (X-KEYSMITH-TOKEN)
                  │
                  ▼
       [ 2. Verify CRC Checksum ]
  Calculates CRC32 checksum in memory.
  If invalid ──► Immediately returns 401 Unauthorized (No DB hit!)
                  │
                  ▼
       [ 3. Database Lookup by Prefix ]
  Indexed select_related("user") and prefetch_related("scopes").
  If token row not found ──► Returns 401 (InvalidToken)
                  │
                  ▼
       [ 4. Status & Expiration Check ]
  Checks revoked == True, purged == True, or expires_at < now.
  If failed ──► Returns 401 (RevokedToken / ExpiredToken)
                  │
                  ▼
       [ 5. Constant-Time Hash Verification ]
  Runs hasher.verify(secret, token.key).
  Timing-safe comparison prevents side-channel attacks.
                  │
                  ▼
       [ 6. Debounced Usage Tracking ]
  Checks LAST_USED_UPDATE_INTERVAL threshold.
  Updates last_used_at in DB only if needed.
                  │
                  ▼
          View Execution
```

---

## Sending Credentials

### 1. Standard `Authorization` Header *(Recommended)*

Clients can supply credentials using standard HTTP authorization headers:

```http
Authorization: Bearer tok_a1B2c3D4:3e8f...c89012
```

Or using the `Token` keyword:

```http
Authorization: Token tok_a1B2c3D4:3e8f...c89012
```

### 2. Custom Header

Alternatively, clients can provide the token in the header configured by `HEADER_NAME` (default: `X-KEYSMITH-TOKEN`):

```http
X-KEYSMITH-TOKEN: tok_a1B2c3D4:3e8f...c89012
```

### 3. Query Parameter *(Optional)*

If you are building webhook endpoints where clients cannot modify headers, you can enable query string tokens in `settings.py`:

```python
KEYSMITH = {
    "ALLOW_QUERY_PARAM": True,
    "QUERY_PARAM_NAME": "api_key",
}
```

```http
GET /api/webhook/?api_key=tok_a1B2c3D4:3e8f...c89012
```

!!! warning "Query Parameter Security"
    URLs are frequently stored in server logs, browser histories, and proxy logs. Avoid query parameter tokens unless strictly necessary for third-party webhook integrations.

---

## High-Performance Optimizations

Keysmith is built for high-throughput production workloads:

### 1. In-Memory Checksum (Fail-Fast)

Every valid token ends with a 6-character CRC checksum calculated over its prefix and secret.

If an attacker scans your API with random strings, Keysmith's CRC check detects the forgery in **microseconds** without performing a database lookup. Your database connections remain available for legitimate users.

### 2. Debounced Usage Tracking (`LAST_USED_UPDATE_INTERVAL`)

Updating `token.last_used_at` on every single HTTP request causes severe database write amplification and connection pool saturation under heavy traffic.

Keysmith includes intelligent write debouncing configured via `LAST_USED_UPDATE_INTERVAL` (default: `60` seconds):

```python
KEYSMITH = {
    # Only update last_used_at in the database once every 60 seconds per token
    "LAST_USED_UPDATE_INTERVAL": 60,
}
```

- If a token handles **10,000 requests per minute**, Keysmith writes to the database **exactly once** instead of 10,000 times!
- The in-memory token instance in your request handler always reflects the latest activity.

### 3. Elimination of Row Locks (`select_for_update`)

Older token systems wrap authentication in `select_for_update` database transactions, creating database deadlocks when multiple parallel requests use the same token.

Keysmith performs standard non-locking reads using `select_related("user")` and `prefetch_related("scopes")`, ensuring zero row contention under concurrent load.

---

## Error Handling & RFC 9110 Compliance

When an authentication check fails, Keysmith responds with an RFC 9110 compliant challenge:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/json

{
  "detail": "This token has expired. Please rotate or request a new token."
}
```

Specific error exceptions raised:

| Exception | Condition | Message |
| :--- | :--- | :--- |
| `InvalidToken` | Checksum failed, missing token, or prefix not in database | *"Invalid token format or token does not exist."* |
| `RevokedToken` | `token.revoked == True` or `token.purged == True` | *"This token has been revoked."* |
| `ExpiredToken` | `token.expires_at < timezone.now()` | *"This token has expired. Please rotate or request a new token."* |

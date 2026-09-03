# Django Keysmith

<p class="ks-lead" markdown>

**Hashed API key authentication and lifecycle management for Django & DRF.** Issue, rotate, revoke, and audit machine credentials without building your own key infrastructure.

</p>

```bash
pip install django-keysmith
```

<div class="ks-features" markdown>

<div class="ks-feature" markdown>

**Hashed Secrets at Rest**
One-way PBKDF2 or SHA-256 hashing. Secrets are only shown once upon creation and never stored in plain text.

</div>

<div class="ks-feature" markdown>

**Complete Lifecycle API**
`create_token`, `rotate_token`, `revoke_token`, and `purge_token` available via Python services, Django Admin, and CLI.

</div>

<div class="ks-feature" markdown>

**Django & DRF Native**
Works seamlessly via Django middleware & decorators or Django REST Framework authentication & permission classes.

</div>

<div class="ks-feature" markdown>

**High-Performance Debouncing**
Debounced usage tracking (`last_used_at`) slashes database writes by >95% on read-heavy workloads.

</div>

<div class="ks-feature" markdown>

**Fine-Grained Scopes**
Leverage Django's standard `auth.Permission` system to enforce endpoint capabilities per token.

</div>

<div class="ks-feature" markdown>

**Built-In Audit Trail**
Track authentication attempts, IP addresses, client headers, and token lifecycle events automatically.

</div>

</div>

---

## In 30 Seconds

Here is how simple it is to protect an API endpoint:

=== "Django REST Framework"

    ```python
    # views.py
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from keysmith.drf.permissions import RequireKeysmithToken

    class MetricsView(APIView):
        permission_classes = [RequireKeysmithToken]

        def get(self, request):
            return Response({
                "status": "healthy",
                "token_id": request.auth.prefix,
                "issued_to": str(request.user),
            })
    ```

=== "Standard Django"

    ```python
    # views.py
    from django.http import JsonResponse
    from keysmith.django.decorator import keysmith_required

    @keysmith_required
    def metrics_view(request):
        return JsonResponse({
            "status": "healthy",
            "token_id": request.keysmith_token.prefix,
            "issued_to": str(request.keysmith_user),
        })
    ```

### 1. Issue a token from your terminal

```bash
python manage.py create_token --name "Monitoring Agent" --user deployer
```

```text
Token created successfully!
--------------------------------------------------------------------------------
Prefix:     tok_a1B2c3D4
Secret:     tok_a1B2c3D4:3e8f...c89012 (Save this now - it will not be shown again!)
Expires At: 2026-12-02 14:30:00 UTC
--------------------------------------------------------------------------------
```

### 2. Make an authenticated request

=== "cURL"

    ```bash
    curl -H "Authorization: Bearer tok_a1B2c3D4:3e8f...c89012" \
      http://localhost:8000/api/metrics/
    ```

=== "HTTPie"

    ```bash
    http http://localhost:8000/api/metrics/ \
      "Authorization: Bearer tok_a1B2c3D4:3e8f...c89012"
    ```

=== "Python (HTTPX)"

    ```python
    import httpx

    headers = {"Authorization": "Bearer tok_a1B2c3D4:3e8f...c89012"}
    response = httpx.get("http://localhost:8000/api/metrics/", headers=headers)
    print(response.json())
    ```

### 3. Response

```json
{
  "status": "healthy",
  "token_id": "tok_a1B2c3D4",
  "issued_to": "deployer"
}
```

---

## The Problem Keysmith Solves

Static API keys hardcoded in `.env` files or application settings work until they don't:

- **Rotation means redeployment**: Updating an API key requires cycling production servers.
- **Revocation is dangerous**: If a credential leaks on GitHub, revoking it involves messy grep-and-replace deployments.
- **No visibility**: You can't tell which partner, microservice, or integration called your API, or when a key was last active.
- **No scoping**: Every key has blanket access to everything.

**Keysmith treats API tokens as first-class database entities with cryptographic safety:**
- Secrets are hashed at rest using PBKDF2-SHA512 or HMAC-SHA256 (identical to password hashing).
- Tokens can be issued, rotated, or revoked instantaneously via Django Admin, Python services, or CLI without server restarts.
- Fast fail-fast checksum validation discards forged keys before querying the database.
- Audit records log IP addresses, user agents, paths, and status codes for every authentication attempt.

---

## How Authentication Works

Keysmith validates incoming requests through an optimized 4-step pipeline:

```text
Incoming Request
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Header Extraction                                         │
│    Reads Authorization: Bearer <token> (or X-KEYSMITH-TOKEN) │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Fail-Fast Checksum Verification (CRC32)                   │
│    Validates the 6-character checksum. Invalid tokens fail   │
│    immediately without touching your database.               │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Indexed DB Lookup & Constant-Time Hash Check              │
│    Fetches token row by prefix. Verifies state (not revoked, │
│    not purged, not expired), then constant-time hashes.      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Request Context & Scope Enforcement                       │
│    Attaches token & user, debounces last_used_at in DB,      │
│    and enforces required permission scopes.                  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
                          Your View
```

!!! info "Unified Architecture"
    Both standard Django views (via middleware/decorators) and Django REST Framework views (via authentication classes) share the exact same underlying validation engine (`authenticate_token`). Behavior is completely consistent across your codebase.

---

## Token Anatomy

Every Keysmith token contains three distinct components engineered for speed, security, and human readability:

<div class="ks-token-anatomy">

<div class="ks-token-pill">
  <span class="ks-token-part ks-token-part--prefix" title="Prefix (12 chars)">tok_a1B2c3D4</span>
  <span class="ks-token-part ks-token-part--sep">:</span>
  <span class="ks-token-part ks-token-part--secret" title="Secret (32 chars)">9aK2mX7pQ1rT4vW8yZ0bC3dF6hJ5nL8s</span>
  <span class="ks-token-part ks-token-part--crc" title="CRC32 Checksum (6 digits)">481029</span>
</div>

<div class="ks-token-legend">

<div class="ks-token-legend-card">
<strong><span class="ks-token-dot ks-token-dot--prefix"></span> Prefix (12 chars)</strong>
<p><code>tok_a1B2c3D4</code> &mdash; Indexed database column. Enables instant <code>O(1)</code> lookup without full-table scanning or decrypting.</p>
</div>

<div class="ks-token-legend-card">
<strong><span class="ks-token-dot ks-token-dot--secret"></span> Secret (32 chars)</strong>
<p><code>9aK2mX...nL8s</code> &mdash; High-entropy credential. Hashed at rest using PBKDF2 or SHA-256; never stored in plaintext.</p>
</div>

<div class="ks-token-legend-card">
<strong><span class="ks-token-dot ks-token-dot--crc"></span> Checksum (6 digits)</strong>
<p><code>481029</code> &mdash; CRC32 checksum. Validated in memory in microseconds to reject forged tokens before touching the database.</p>
</div>

</div>

</div>

| Component | In Database? | Verification Method | Purpose |
| :--- | :---: | :--- | :--- |
| **Prefix** (`tok_...`) | **Yes (Indexed)** | Indexed SQL query | Instant lookup key without decrypting credentials. |
| **Secret** | **Hash only** | Constant-time hash verification | Confidential secret verifying authenticity. |
| **Checksum** | **No** | In-memory CRC32 validation | Discards malformed/forged keys before hitting DB. |

---

## Where to Next?

<div class="ks-features" markdown>

<div class="ks-feature" markdown>

**[Installation Guide](getting-started/install.md)**
Set up dependencies, register the app, run migrations, and verify your installation.

</div>

<div class="ks-feature" markdown>

**[Step-by-Step Tutorial](getting-started/tutorial.md)**
Walk through an end-to-end guide creating tokens, protecting views, and testing responses.

</div>

<div class="ks-feature" markdown>

**[Django REST Framework](integrations/drf.md)**
Configure DRF authentication, permissions, and token rate throttling.

</div>

<div class="ks-feature" markdown>

**[CLI Commands](reference/commands.md)**
Learn how to create, list, and revoke tokens from CI/CD scripts or terminal.

</div>

</div>

---

## Compatibility

- **Python**: `>= 3.10` (Python 3.10, 3.11, 3.12, 3.13)
- **Django**: `4.2 LTS`, `5.1`, `5.2 LTS` (`>= 4.2, < 6.0`)
- **Django REST Framework**: `>= 3.15` *(optional)*

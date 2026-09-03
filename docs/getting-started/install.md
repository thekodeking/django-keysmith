# Installation

Get up and running with `django-keysmith` in less than two minutes.

---

## 1. Install the Package

Choose your preferred package manager:

=== "uv"

    ```bash
    # Django standard views
    uv add django-keysmith

    # Or with Django REST Framework support
    uv add "django-keysmith[drf]"
    ```

=== "pip"

    ```bash
    # Django standard views
    pip install django-keysmith

    # Or with Django REST Framework support
    pip install "django-keysmith[drf]"
    ```

=== "poetry"

    ```bash
    # Django standard views
    poetry add django-keysmith

    # Or with Django REST Framework support
    poetry add django-keysmith --extras drf
    ```

---

## 2. Configure Django Settings

Add `"keysmith"` to your `INSTALLED_APPS`:

```python
# settings.py

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ...
    "keysmith",
]
```

### Add the Authentication Middleware

Add `KeysmithAuthenticationMiddleware` right after Django's `AuthenticationMiddleware`:

```python
# settings.py

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Keysmith authentication middleware:
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
```

!!! tip "Middleware Behavior"
    `KeysmithAuthenticationMiddleware` extracts credentials and populates `request.keysmith_token` and `request.keysmith_user`. It **never** blocks unauthenticated public traffic on its own. Views opt into protection using the `@keysmith_required` decorator or DRF permission classes.

---

## 3. Apply Database Migrations

Run migrations to create the token and audit log tables:

```bash
python manage.py migrate
```

Keysmith creates two tables in your database:

1. `keysmith_token`: Stores token metadata (prefixes, hashes, scopes, expiry timestamps).
2. `keysmith_token_audit_log`: Stores audit event records for authentication attempts and token lifecycle events.

---

## 4. (Optional) Configure DRF Defaults

If you are using Django REST Framework and want Keysmith authentication enabled across all views by default, update your `REST_FRAMEWORK` dictionary:

```python
# settings.py

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

---

## 5. Verify Your Installation

Generate a test token directly from your terminal using the built-in CLI management command:

```bash
python manage.py create_token --name "smoke-test"
```

You should see output similar to:

```text
Token created successfully!
--------------------------------------------------------------------------------
Prefix:     tok_v7K9p2X1
Secret:     tok_v7K9p2X1:4b8109d...38a912 (Save this now - it will not be shown again!)
Expires At: 2026-12-02 14:15:00 UTC
--------------------------------------------------------------------------------
```

!!! warning "Store the raw secret safely"
    The printed string is the **only time** the full secret will ever be displayed. Keysmith stores a one-way cryptographic hash in your database.

---

## Built-In System Checks

Keysmith registers automated system checks that run whenever you execute `python manage.py check`:

| Check ID | Level | What It Guards Against |
| :--- | :---: | :--- |
| `keysmith.E001`–`E003` | **Error** | Swappable model misconfigurations or contract violations |
| `keysmith.E004`–`E007` | **Error** | Invalid `TOKEN_PREFIX`, `TOKEN_SECRET_LENGTH`, or `HASH_ITERATIONS` (< 10,000) |
| `keysmith.W001` | **Warning** | Using SQLite with concurrency in high-write environments |
| `keysmith.W002` | **Warning** | Unknown or misspelled keys in your `KEYSMITH` settings |

---

**Next:** Head over to the **[Step-by-Step Tutorial](tutorial.md)** to protect your first view and make authenticated requests!

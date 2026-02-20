# Installation

This page covers package installation and the minimum framework wiring required before creating tokens.

## Requirements

Make sure your runtime versions are compatible before installation.

- Python `>=3.9`
- Django `>=4.0`

## Install

Install the base package when you only need Django integration.

```bash
pip install django-keysmith
```

With DRF integration:

```bash
pip install "django-keysmith[drf]"
```

The DRF extra is optional and only needed when using Keysmith's DRF classes.

## Django Setup

After installing, register the app and middleware in settings so token context is available on requests.

Add the app:

```python
INSTALLED_APPS = [
    # ...
    "keysmith",
]
```

Add middleware (recommended for plain Django views):

```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "keysmith.django.middleware.KeysmithAuthenticationMiddleware",
]
```

Run migrations:

```bash
python manage.py migrate
```

## Optional DRF Setup

If your project serves DRF endpoints, add the authentication and permission defaults below. This gives consistent behavior across endpoints without per-view duplication.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "keysmith.drf.auth.KeysmithAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "keysmith.drf.permissions.RequireKeysmithToken",
    ],
}
```

## Verify Quickly

A quick shell check confirms token creation and schema state.

```bash
python manage.py shell
```

```python
from keysmith.services.tokens import create_token

token, raw_token = create_token(name="dev-token")
print(token.prefix)
print(raw_token)
```

Store `raw_token` immediately. It cannot be recovered from the database later.

Next: [Quick Start](quickstart.md)

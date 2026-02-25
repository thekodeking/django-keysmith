from django.core.checks import Error, Warning, register

from keysmith.models.utils import get_audit_log_model, get_token_model


@register()
def keysmith_model_contract_checks(app_configs, **kwargs):
    """Ensure configured token and audit models expose required fields/methods."""
    errors = []
    token_model = get_token_model()
    audit_model = get_audit_log_model()

    required_token_fields = (
        "key",
        "prefix",
        "revoked",
        "purged",
        "expires_at",
        "last_used_at",
        "user",
    )
    required_token_methods = ("can_authenticate",)
    required_audit_fields = (
        "token",
        "action",
        "path",
        "method",
        "status_code",
        "ip_address",
        "user_agent",
        "extra",
        "created_at",
    )

    for field_name in required_token_fields:
        try:
            token_model._meta.get_field(field_name)
        except Exception:
            errors.append(
                Error(
                    f"Token model is missing required field: '{field_name}'.",
                    id="keysmith.E001",
                )
            )

    for method_name in required_token_methods:
        if not hasattr(token_model, method_name):
            errors.append(
                Error(
                    f"Token model is missing required method: '{method_name}'.",
                    id="keysmith.E002",
                )
            )

    for field_name in required_audit_fields:
        try:
            audit_model._meta.get_field(field_name)
        except Exception:
            errors.append(
                Error(
                    f"Audit log model is missing required field: '{field_name}'.",
                    id="keysmith.E003",
                )
            )

    return errors


@register()
def check_sqlite_concurrency(app_configs, **kwargs):
    """Warn when SQLite is the default database.

    Keysmith's authenticate_token() uses SELECT FOR UPDATE inside an atomic
    transaction to safely update last_used_at.  PostgreSQL and MySQL honour
    row-level locks, so concurrent requests for different tokens proceed in
    parallel.  SQLite escalates any SELECT FOR UPDATE to a *full table lock*,
    which means concurrent authentication attempts for the *same or different*
    tokens all serialise — and Django's default lock timeout of 0 ms causes
    the waiting transactions to raise OperationalError immediately.

    This is harmless for sequential workloads (e.g. a single-worker dev
    server) but will surface as spurious auth failures under multi-threaded
    or multi-process concurrency.  Use PostgreSQL or MySQL in production.
    """
    from django.db import connections

    try:
        vendor = connections["default"].vendor
    except Exception:
        return []

    if vendor == "sqlite":
        return [
            Warning(
                "Keysmith uses SELECT FOR UPDATE inside authenticate_token(), "
                "which SQLite escalates to a full table lock. "
                "Concurrent authentication requests will raise OperationalError "
                "under multi-threaded or multi-process load. "
                "Use PostgreSQL or MySQL for production deployments.",
                hint=(
                    "Switch DATABASE ENGINE to 'django.db.backends.postgresql' "
                    "or 'django.db.backends.mysql', or run your dev server with "
                    "a single worker and no concurrent auth load."
                ),
                id="keysmith.W001",
            )
        ]
    return []

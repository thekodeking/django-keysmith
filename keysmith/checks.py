from django.core.checks import Error, register

from keysmith.models.utils import get_audit_log_model, get_token_model


@register()
def keysmith_model_contract_checks(app_configs, **kwargs):
    errors = []
    token_model = get_token_model()
    audit_model = get_audit_log_model()

    required_token_fields = (
        "key",
        "prefix",
        "hint",
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

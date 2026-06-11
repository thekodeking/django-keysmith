from __future__ import annotations

import logging
from typing import Any

from keysmith.hooks import load_hook
from keysmith.models.utils import get_audit_log_model
from keysmith.settings import keysmith_settings

logger = logging.getLogger("keysmith.audit")


def _get_ip_address(request) -> str | None:
    if getattr(keysmith_settings, "TRUST_PROXIES", False):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip() or None

    return request.META.get("REMOTE_ADDR")


def _request_context(request, status_code: int) -> dict[str, Any]:
    return {
        "path": request.path,
        "method": request.method,
        "status_code": status_code,
        "ip_address": _get_ip_address(request),
        "user_agent": request.META.get("HTTP_USER_AGENT"),
    }


def log_audit_event(
    *,
    action: str,
    request=None,
    token=None,
    status_code: int = 0,
    extra: dict[str, Any] | None = None,
) -> None:
    """Write an audit row if enabled, swallowing failures to avoid auth disruption."""
    if not keysmith_settings.ENABLE_AUDIT_LOGGING:
        return

    try:
        payload = (
            _request_context(request, status_code)
            if request
            else {
                "path": "",
                "method": "",
                "status_code": status_code,
                "ip_address": None,
                "user_agent": None,
            }
        )

        audit_log_hook = load_hook("AUDIT_LOG_HOOK")
        if audit_log_hook is not None:
            audit_log_hook(
                action=action,
                token=token,
                request=request,
                status_code=status_code,
                extra=extra,
                payload=payload,
            )
            return

        AuditLog = get_audit_log_model()
        AuditLog.objects.create(
            token=token,
            action=action,
            path=payload["path"],
            method=payload["method"],
            status_code=payload["status_code"],
            ip_address=payload["ip_address"],
            user_agent=payload["user_agent"],
            extra=extra or {},
        )
    except Exception:
        # audit logging must never interrupt auth.
        logger.exception("Failed to write Keysmith audit log entry")

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AbstractToken(models.Model):
    class TokenType(models.TextChoices):
        USER = "user", "User"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tokens",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )

    token_type = models.CharField(
        max_length=10,
        choices=TokenType.choices,
        default=TokenType.USER,
    )

    scopes = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        help_text="Django permissions associated with this token",
    )

    key = models.CharField(max_length=256, unique=True)

    prefix = models.CharField(max_length=12, db_index=True)
    hint = models.CharField(max_length=8)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    revoked = models.BooleanField(default=False)
    purged = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked"]),
        ]

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and timezone.now() > self.expires_at)

    @property
    def is_active(self) -> bool:
        return not self.revoked and not self.purged and not self.is_expired

    def can_authenticate(self) -> bool:
        """
        Canonical check used by auth pipeline.
        Custom models MUST preserve this semantic.
        """
        return self.is_active

    def mark_used(self, *, commit: bool = True) -> None:
        self.last_used_at = timezone.now()
        if commit:
            self.save(update_fields=["last_used_at"])

    def __str__(self):
        return f"{self.name} ({self.token_type})"


from django.db import models


class AbstractTokenAuditLog(models.Model):
    """
    Contract for token audit logging.

    This model records both token lifecycle events (revoke, rotate)
    and request-level authentication attempts.
    """

    ACTION_AUTH_SUCCESS = "auth_success"
    ACTION_AUTH_FAILED = "auth_failed"
    ACTION_REVOKED = "revoked"
    ACTION_ROTATED = "rotated"

    ACTION_CHOICES = [
        (ACTION_AUTH_SUCCESS, "Authentication Success"),
        (ACTION_AUTH_FAILED, "Authentication Failed"),
        (ACTION_REVOKED, "Token Revoked"),
        (ACTION_ROTATED, "Token Rotated"),
    ]

    id = models.BigAutoField(primary_key=True)

    token = models.ForeignKey(
        "keysmith.Token",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=64,
        choices=ACTION_CHOICES,
    )

    path = models.TextField(
        help_text="Request path (without domain)",
    )

    method = models.CharField(
        max_length=10,
        help_text="HTTP method",
    )

    status_code = models.PositiveSmallIntegerField(
        help_text="HTTP response status code",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context (errors, reason, actor, etc.)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        token = self.token_id or "unknown-token"
        return f"{self.action} [{self.method} {self.path}] ({token})"

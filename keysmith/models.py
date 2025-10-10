import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Token(models.Model):
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
        max_length=10, choices=TokenType.choices, default=TokenType.USER
    )

    scopes = models.ManyToManyField("auth.Permission", blank=True)

    key = models.CharField(max_length=256, unique=True)

    prefix = models.CharField(max_length=12, db_index=True)
    hint = models.CharField(max_length=8)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    revoked = models.BooleanField(default=False)
    purged = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.token_type})"

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and timezone.now() > self.expires_at)

    @property
    def is_active(self) -> bool:
        return not self.revoked and not self.purged and not self.is_expired

    def mark_used(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])


class TokenAuthLog(models.Model):
    class Method(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        DELETE = "DELETE", "DELETE"
        PATCH = "PATCH", "PATCH"
        OPTIONS = "OPTIONS", "OPTIONS"
        HEAD = "HEAD", "HEAD"
        TRACE = "TRACE", "TRACE"
        CONNECT = "CONNECT", "CONNECT"

    token = models.ForeignKey("Token", on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.TextField()
    method = models.CharField(choices=Method.choices, max_length=10)
    status_code = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Log for {self.token} @ {self.created_at}"

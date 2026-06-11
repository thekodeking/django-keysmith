from django.db import models

from keysmith.models.base import AbstractToken, AbstractTokenAuditLog


class TestResource(models.Model):
    """A simple model for testing API endpoints with token authentication."""

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class CustomToken(AbstractToken):
    custom_field = models.CharField(max_length=50, default="default_value")

    class Meta(AbstractToken.Meta):
        db_table = "tests_custom_token"


class CustomTokenAuditLog(AbstractTokenAuditLog):
    custom_log_field = models.CharField(max_length=50, default="default_log_value")

    class Meta(AbstractTokenAuditLog.Meta):
        db_table = "tests_custom_token_audit_log"

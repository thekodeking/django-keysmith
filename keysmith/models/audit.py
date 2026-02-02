from keysmith.models.base import AbstractTokenAuditLog


class TokenAuditLog(AbstractTokenAuditLog):
    """
    Default Keysmith audit log model.
    """

    class Meta(AbstractTokenAuditLog.Meta):
        db_table = "keysmith_token_audit_log"

from django.contrib import admin

from keysmith.models import Token, TokenAuditLog
from keysmith.services.tokens import revoke_token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "token_type",
        "user",
        "revoked",
        "purged",
        "expires_at",
        "last_used_at",
        "created_at",
    )
    list_filter = (
        "token_type",
        "revoked",
        "purged",
        "expires_at",
        "created_at",
    )
    search_fields = (
        "name",
        "prefix",
        "hint",
        "user__username",
        "user__email",
    )
    readonly_fields = (
        "id",
        "key",
        "prefix",
        "hint",
        "created_at",
        "last_used_at",
    )
    actions = (
        "revoke_selected_tokens",
        "purge_selected_tokens",
    )

    @admin.action(description="Revoke selected tokens")
    def revoke_selected_tokens(self, request, queryset):
        updated = 0
        for token in queryset.iterator():
            if token.revoked:
                continue
            revoke_token(token, request=request, actor=request.user)
            updated += 1

        self.message_user(request, f"Revoked {updated} token(s).")

    @admin.action(description="Purge selected tokens")
    def purge_selected_tokens(self, request, queryset):
        updated = 0
        for token in queryset.iterator():
            if token.purged:
                continue
            revoke_token(token, purge=True, request=request, actor=request.user)
            updated += 1

        self.message_user(request, f"Purged {updated} token(s).")


@admin.register(TokenAuditLog)
class TokenAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "action",
        "token",
        "method",
        "path",
        "status_code",
        "ip_address",
        "created_at",
    )
    list_filter = (
        "action",
        "method",
        "status_code",
        "created_at",
    )
    search_fields = (
        "path",
        "ip_address",
        "user_agent",
        "token__prefix",
        "token__hint",
    )
    readonly_fields = (
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
    date_hierarchy = "created_at"

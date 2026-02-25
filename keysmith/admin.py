from django.contrib import admin, messages
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from keysmith.models import Token, TokenAuditLog
from keysmith.services.tokens import create_token, purge_token, revoke_token, rotate_token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "token_type",
        "token_id_display",
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
        "user__username",
        "user__email",
    )
    readonly_fields = (
        "id",
        "key",
        "prefix",
        "created_at",
        "last_used_at",
        "rotate_token_link",
    )
    actions = (
        "revoke_selected_tokens",
        "purge_selected_tokens",
        "rotate_selected_tokens",
    )

    _RAW_TOKEN_SESSION_PREFIX = "keysmith.raw_token."

    @admin.display(description="Token ID", ordering="prefix")
    def token_id_display(self, obj):
        return obj.prefix

    @admin.display(description="Rotate")
    def rotate_token_link(self, obj):
        if not obj.pk or obj.revoked or obj.purged:
            return "-"
        url = reverse(
            "admin:keysmith_token_rotate",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )
        return format_html('<a class="button" href="{}">Rotate Token</a>', url)

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "name",
                "description",
                "token_type",
                "created_by",
                "user",
                "scopes",
                "expires_at",
            )
        return (
            "id",
            "name",
            "description",
            "token_type",
            "created_by",
            "user",
            "scopes",
            "key",
            "prefix",
            "expires_at",
            "last_used_at",
            "revoked",
            "purged",
            "created_at",
            "rotate_token_link",
        )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            ro.extend(["name", "description", "token_type", "created_by", "user", "scopes"])
        return tuple(ro)

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        token, raw_token = create_token(
            name=form.cleaned_data["name"],
            description=form.cleaned_data.get("description", ""),
            created_by=form.cleaned_data.get("created_by"),
            user=form.cleaned_data.get("user"),
            scopes=form.cleaned_data.get("scopes"),
            expires_at=form.cleaned_data.get("expires_at"),
            token_type=form.cleaned_data.get("token_type"),
            request=request,
        )

        # Keep Django admin add flow working against the persisted instance.
        obj.pk = token.pk
        obj._state.adding = False
        obj._state.db = token._state.db

        request._keysmith_created_token = token
        request._keysmith_raw_token = raw_token

    def save_related(self, request, form, formsets, change):
        # Token creation is handled by create_token(), including scopes.
        if change:
            super().save_related(request, form, formsets, change)

    def response_add(self, request, obj, post_url_continue=None):
        token = getattr(request, "_keysmith_created_token", None)
        raw_token = getattr(request, "_keysmith_raw_token", None)
        if token is None or raw_token is None:
            return super().response_add(request, obj, post_url_continue=post_url_continue)

        session_key = f"{self._RAW_TOKEN_SESSION_PREFIX}{token.pk}"
        request.session[session_key] = raw_token

        token_created_url = reverse(
            "admin:keysmith_token_token_created",
            args=[token.pk],
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(token_created_url)

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "<path:object_id>/token-created/",
                self.admin_site.admin_view(self.token_created_view),
                name="keysmith_token_token_created",
            ),
            path(
                "<path:object_id>/rotate/",
                self.admin_site.admin_view(self.token_rotated_view),
                name="keysmith_token_rotate",
            ),
        ]
        return extra + urls

    def token_created_view(self, request, object_id):
        token = self.get_object(request, object_id)
        if token is None:
            raise Http404("Token does not exist")

        if not self.has_view_or_change_permission(request, obj=token):
            raise Http404("Not allowed")

        session_key = f"{self._RAW_TOKEN_SESSION_PREFIX}{token.pk}"
        raw_token = request.session.pop(session_key, None)

        if not raw_token:
            messages.warning(
                request,
                "The token value is only shown once and is no longer available.",
            )
            change_url = reverse(
                "admin:keysmith_token_change",
                args=[token.pk],
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(change_url)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": token,
            "token": token,
            "raw_token": raw_token,
            "title": "Token created",
        }
        return TemplateResponse(request, "admin/keysmith/token/token_created.html", context)

    def token_rotated_view(self, request, object_id):
        """Handle single-token rotation from the change form."""
        token = self.get_object(request, object_id)
        if token is None:
            raise Http404("Token does not exist")

        if not self.has_change_permission(request, obj=token):
            raise Http404("Not allowed")

        if token.revoked or token.purged:
            messages.error(request, "Cannot rotate a revoked or purged token.")
            change_url = reverse(
                "admin:keysmith_token_change",
                args=[token.pk],
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(change_url)

        new_raw = rotate_token(token, request=request, actor=request.user)

        session_key = f"{self._RAW_TOKEN_SESSION_PREFIX}{token.pk}"
        request.session[session_key] = new_raw

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": token,
            "token": token,
            "raw_token": new_raw,
            "title": "Token rotated",
            "subtitle": "The old token value is now invalid.",
        }
        return TemplateResponse(request, "admin/keysmith/token/token_created.html", context)

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
            purge_token(token, request=request, actor=request.user)
            updated += 1

        self.message_user(request, f"Purged {updated} token(s).")

    @admin.action(description="Rotate selected tokens")
    def rotate_selected_tokens(self, request, queryset):
        rotated = 0
        skipped = 0
        for token in queryset.iterator():
            if token.revoked or token.purged:
                skipped += 1
                continue
            rotate_token(token, request=request, actor=request.user)
            rotated += 1

        msg = f"Rotated {rotated} token(s)."
        if skipped:
            msg += f" Skipped {skipped} revoked/purged token(s)."
        self.message_user(request, msg)


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

# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Changed

- Documentation rebuilt from scratch for Zensical: new site structure (getting started → topics → integrations → reference → extending), fresh content, and updated theme configuration.

---

## [0.1.1]

Maintenance release.

---

## [0.1.0]

Initial public release.

### Added

- Token creation with PBKDF2-SHA512 hashed secrets
- Lifecycle operations: `rotate_token`, `revoke_token`, `purge_token`
- Optional token expiry via `DEFAULT_EXPIRY_DAYS` or `expires_at`
- Audit logging for authentication and lifecycle events
- Scope model backed by Django `Permission` codenames
- Plain Django integration: middleware, `@keysmith_required`, `@keysmith_scopes`
- DRF integration: `KeysmithAuthentication`, `RequireKeysmithToken`, `HasKeysmithScopes`, `ScopedPermission`
- Django admin with one-time raw token display, rotate/revoke/purge actions
- Swappable token and audit models with Django system checks
- Extensibility hooks: `RATE_LIMIT_HOOK`, `DRF_THROTTLE_HOOK`, `AUDIT_LOG_HOOK`
- `prune_audit_logs` management command

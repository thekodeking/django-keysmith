# Changelog

## [0.1.2]

### Added

- Audit log hooks and proxy trust settings: `AUDIT_LOG_HOOK`, `AUDIT_LOG_RETENTION_DAYS`,
  `TRUST_PROXIES`
- `prune_audit_logs` management command
- Test infrastructure: `CustomToken`/`CustomTokenAuditLog` test models, concurrency tests, system
  check tests, IP extraction tests, database URL support in test settings
- PostgreSQL integration tests in CI
- More Django system checks and updated admin template

### Changed

- **Breaking:** Updated database schema with unique token prefixes, performance indices for
  `TokenAuditLog`, and updated `ForeignKey` configurations
- Refactored token generation with retry logic for prefix collisions, dynamic related names,
  enhanced scope permission resolution, and database indexes for audit logs
- Updated `keysmith_required` decorator to check `keysmith_token` property
- Formatted migration files
- Updated pyproject dependency groups and metadata

### Fixed

- Updated SQLite test case compatibility

### Documentation

- Revamped documentation site structure (getting started → topics → integrations → reference →
  extending)

### Dependencies

- Bumped urllib3 from 2.5.0 to 2.7.0

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
- DRF integration: `KeysmithAuthentication`, `RequireKeysmithToken`, `HasKeysmithScopes`,
  `ScopedPermission`
- Django admin with one-time raw token display, rotate/revoke/purge actions
- Swappable token and audit models with Django system checks
- Extensibility hooks: `RATE_LIMIT_HOOK`, `DRF_THROTTLE_HOOK`, `AUDIT_LOG_HOOK`
- `prune_audit_logs` management command

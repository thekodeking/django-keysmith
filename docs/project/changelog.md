# Changelog

## [0.1.3]

### Security
- Hardened admin token rotation: converted single-token rotation to require `POST` with CSRF validation and an intermediate confirmation page, preventing prefetch or CSRF attacks.
- Disabled destructive bulk token rotation action in Django admin to prevent permanent credential loss.
- Added strict IP validation via `ipaddress` to prevent malformed or spoofed IP values from failing database saves.
- Added `CLIENT_IP_HEADER` and `CLIENT_IP_HOOK` settings for trusted, spoof-proof reverse proxy IP resolution.

### Performance & Concurrency
- Removed `select_for_update()` and row-level locking from `authenticate_token()`, eliminating lock contention and table-lock issues on concurrent workloads.
- Added debounced `last_used_at` database updates via `LAST_USED_UPDATE_INTERVAL` (default: 60s), slashing database writes by >95% on read-heavy workloads.
- Added `select_related("user")` and `prefetch_related("scopes")` during authentication to eliminate downstream N+1 queries.
- Added fast hashing backends `SHA256TokenHasher` and `HMACSHA256TokenHasher` for sub-millisecond authentication on high-throughput APIs.

### Features & Integrations
- Added standard `Authorization: Bearer <token>` and `Authorization: Token <token>` header support to plain Django middleware and DRF.
- Added CLI management commands: `create_token`, `revoke_token`, and `list_tokens`.
- Added DRF `KeysmithTokenRateThrottle` for token prefix rate limiting.
- Updated DRF `authenticate_header` to comply with RFC 9110 (`Bearer realm="api"`).
- Added direct callable support for all configuration hooks (`RATE_LIMIT_HOOK`, `DRF_THROTTLE_HOOK`, `AUDIT_LOG_HOOK`, `CLIENT_IP_HOOK`).
- Updated `rotate_token` to accept `expires_at` and automatically renew expired tokens.

### Fixed
- Fixed hardcoded admin URLs in `token_created.html` to support swappable token models using `admin_urls`.
- Fixed `token.last_used_at` in-memory update on authenticated instances.

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

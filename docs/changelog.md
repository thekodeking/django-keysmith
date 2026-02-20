# Changelog

All notable changes to this project are documented here.

## [Unreleased]

This section tracks documentation and code changes that are planned for the next release tag.

### Added

- Native `zensical.toml` site configuration.
- Expanded docs for setup, integration, lifecycle, and API reference.
- Development and security model documentation pages.
- Additional explanatory paragraphs across docs sections for improved readability.

### Changed

- Documentation restructured for task-focused reading.
- API and behavior descriptions aligned with current source implementation.
- Table typography tuned to reduce oversized rendering.

## [0.1.0]

Initial public release of Django Keysmith.

### Added

- Token creation with hashed secrets.
- Rotation and revocation lifecycle operations.
- Optional expiry handling.
- Audit logging for authentication and lifecycle events.
- DRF integration (`KeysmithAuthentication`, permission classes).
- Plain Django integration (middleware and decorators).

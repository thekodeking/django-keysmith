# Security Model

This page summarizes the security assumptions and controls built into Keysmith. It is intended to help teams map library behavior to their internal security requirements.

## Core Guarantees

Keysmith is designed so token misuse is constrained by lifecycle state and secret-handling defaults.

- Token secrets are never stored in plaintext.
- Secret verification uses PBKDF2-SHA512 hashes.
- Token parsing includes checksum validation before DB lookup.
- Revoked, purged, and expired tokens are blocked.

## Authentication Controls

The authentication path is deterministic and efficient, reducing error-prone custom logic in consuming projects.

- Prefix-based indexed lookup keeps token resolution predictable.
- Middleware and DRF integrations share the same validation core.
- Optional hooks allow custom rate-limit and throttle enforcement.

## Auditability

Audit events provide visibility into both request authentication and token lifecycle actions.

Keysmith writes request/lifecycle audit events with optional metadata:

- auth success/failure
- token rotation/revocation
- status code, request path/method, source IP, user agent

## Scope Model

Scopes map directly to Django permission codenames and are evaluated as exact codename membership checks.

Scopes map to Django permission codenames and are attached to tokens.
Use least privilege and separate tokens per integration boundary.

## Operational Recommendations

These practices are strongly recommended for production use.

- Prefer header-based token transport.
- Disable query parameter tokens unless strictly necessary.
- Rotate tokens after incidents.
- Enforce finite token expiry windows.
- Retain audit logs based on your compliance and incident-response needs.

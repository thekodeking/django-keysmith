# Authentication

Keysmith has one core validator (`authenticate_token`) and two integration points:

- `keysmith.django.middleware.KeysmithAuthenticationMiddleware`
- `keysmith.drf.auth.KeysmithAuthentication`

The benefit of this model is predictable behavior across stacks. Whether a request enters via plain Django or DRF, token validity semantics stay the same.

## Validation Pipeline

Each step below is intentionally ordered for fast rejection of malformed input and deterministic DB access.

1. Read token from configured header (or query parameter if enabled).
2. Parse token and verify checksum.
3. Lookup token by `prefix`.
4. Reject revoked/purged/expired tokens.
5. Verify secret hash.
6. Mark token as used (`last_used_at`).

## Error Types

The exception hierarchy lets calling code distinguish credential state issues from malformed input.

- `InvalidToken`: malformed token, unknown prefix, failed hash verify, or missing token.
- `ExpiredToken`: token exists but is expired.
- `RevokedToken`: token is revoked or purged.

All inherit from `TokenAuthError`.

## Middleware Behavior

Middleware is usually the best fit for plain Django projects because it centralizes token extraction and context hydration.

Middleware sets request context fields:

- `request.keysmith_token`
- `request.keysmith_user`
- `request.keysmith_auth_error`

It also emits audit events after response:

- `auth_success`
- `auth_failed`

## DRF Behavior

`KeysmithAuthentication` integrates directly with DRF auth/permission flow and emits audit events itself.

`KeysmithAuthentication`:

- reads token from `request.headers`
- authenticates through `authenticate_token`
- applies optional `DRF_THROTTLE_HOOK`
- returns `(request_user, token)`, using DRF's unauthenticated user object when the token has no user
- writes auth audit events

## Token Format

The token structure supports prefix lookup and checksum validation before hash verification.

```text
<prefix>_<id>:<secret><crc>
```

Examples of parse failures:

- too short
- missing `:`
- missing `_` inside prefix segment
- invalid checksum
- empty secret

## Operational Advice

Treat these as defaults for secure operation in real deployments.

- Prefer headers over query parameters.
- Keep middleware after Django `AuthenticationMiddleware`.
- Monitor failed authentication volume by route/IP.

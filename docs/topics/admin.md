# Django Admin Integration

Keysmith provides a customized, secure administrative interface built into Django's standard admin site.

---

## Token Administration

In the Django Admin (`/admin/keysmith/token/`), administrators can manage credentials with built-in safety rails.

### 1. Token Creation & One-Time Secret Display

When an administrator creates a token:

1. They assign a **Name**, **Linked User** (optional), **Scopes**, and **Expiration Date**.
2. Upon saving, Keysmith displays a one-time banner with the full raw token secret.
3. The raw secret is **never stored** and cannot be viewed again once dismissed.

!!! warning "Copy Immediately"
    Keysmith only saves the cryptographic hash of the secret. Once you navigate away from the creation page, the secret cannot be recovered. If lost, the token must be rotated.

---

### 2. Single-Token Rotation with Confirmation

To rotate an active token:

1. Click into the token change form.
2. Click the **Rotate token** button in the top-right toolbar.
3. A **Confirmation Page** is displayed (*"Are you sure you want to rotate this token? The old credential will stop working immediately"*).
4. After clicking **Confirm Rotation** (via POST request), the new secret is generated and displayed on a one-time view.

!!! info "Why Require POST Confirmation?"
    Modern web browsers and browser extensions aggressively prefetch links (`<link rel="prefetch">`). Requiring an explicit POST confirmation prevents accidental rotations triggered by browser crawlers, prefetching, or cross-site request forgery.

---

### 3. Bulk Actions

From the Token changelist view, administrators can perform bulk operations:

| Action | Supported? | Description |
| :--- | :---: | :--- |
| **Revoke selected tokens** | Yes | Instantly disables selected tokens, setting `revoked = True`. |
| **Purge selected tokens** | Yes | Permanently soft-deletes selected tokens (`purged = True`). |
| **Rotate selected tokens** | **Disabled** | Bulk rotation is intentionally blocked. Because raw secrets can only be displayed once, bulk rotation would result in permanent credential loss for unrecorded tokens. |

---

## Audit Log Inspection

The **Token audit logs** changelist (`/admin/keysmith/tokenauditlog/`) gives administrators full operational visibility:

- **Filter by Action**: Filter by `authenticated`, `auth_failed`, `created`, `rotated`, `revoked`.
- **Filter by Response Code**: Quickly identify spikes in `401 Unauthorized` or `403 Forbidden` responses.
- **Search by Token Prefix or IP**: Trace suspicious traffic from a specific IP address or investigate access history for `tok_a1B2c3D4`.
- **Date Hierarchies**: Drill down into usage by month, day, or hour.

---

## Swappable Token Models

If your application customizes the token model via `TOKEN_MODEL` (e.g. `TOKEN_MODEL = "myapp.CustomToken"`), Keysmith's admin views dynamically adapt using Django's `admin_urls` reversal tags. Your custom fields, list displays, and search filters work out of the box!

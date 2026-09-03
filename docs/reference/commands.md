# CLI Management Commands Reference

Keysmith includes command-line management commands for automated deployments, CI/CD scripts, and administrative maintenance.

---

## `create_token`

Issue a new API token from the terminal and display its one-time raw secret.

```bash
python manage.py create_token --name NAME [options]
```

### Options

| Option | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--name` | `str` | **Required** | Human-readable label for the token (e.g. `"GitHub Actions Deployer"`). |
| `--user` | `str` | `None` | Username of the Django user to link with this token. |
| `--description` | `str` | `""` | Optional descriptive context or notes. |
| `--scopes` | `str` | `None` | Comma-separated list of permission strings (e.g. `"orders.view_order,orders.add_order"`). |
| `--days` | `int` | `90` | Lifetime in days before the token expires. |
| `--system` | flag | `False` | Mark as a system/service token without an associated user account. |

### Examples

```bash
# Standard user token expiring in 60 days:
python manage.py create_token --name "CI Deployer" --user deploy_bot --days 60

# Scoped system token:
python manage.py create_token \
  --name "Stripe Ingestion Worker" \
  --system \
  --scopes "billing.add_invoice,billing.change_invoice"
```

---

## `revoke_token`

Deactivate an existing token by its prefix, preventing any future authentication.

```bash
python manage.py revoke_token PREFIX [--purge]
```

### Options

| Option | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `prefix` | `str` | **Required** | The token's prefix identifier (e.g. `tok_a1B2c3D4`). |
| `--purge` | flag | `False` | Permanently soft-delete (purge) the token record. |

### Examples

```bash
# Soft-revoke a token:
python manage.py revoke_token tok_a1B2c3D4

# Permanently purge a retired token:
python manage.py revoke_token tok_a1B2c3D4 --purge
```

---

## `list_tokens`

Output a formatted table of all tokens with their ID, name, linked user, status, and expiration.

```bash
python manage.py list_tokens [options]
```

### Options

| Option | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--active` | flag | `False` | Display only active tokens (valid, not revoked, not expired). |
| `--revoked` | flag | `False` | Display only revoked or purged tokens. |
| `--expired` | flag | `False` | Display only expired tokens. |
| `--user` | `str` | `None` | Filter tokens issued to a specific username. |

### Example

```bash
python manage.py list_tokens --active
```

Output:

```text
+--------------+-----------------------+------------+---------+---------------------+
| Prefix       | Name                  | User       | Status  | Expires At          |
+--------------+-----------------------+------------+---------+---------------------+
| tok_a1B2c3D4 | Partner Integration   | deploy_bot | Active  | 2026-12-02 14:00:00 |
| tok_9x8w7v6u | Ingestion Worker      | (System)   | Active  | 2026-11-15 09:30:00 |
+--------------+-----------------------+------------+---------+---------------------+
```

---

## `prune_audit_logs`

Delete historical audit log entries older than a specified retention threshold to maintain database performance.

```bash
python manage.py prune_audit_logs [--days N]
```

### Options

| Option | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--days` | `int` | `90` | Retention window in days. Rows older than `now - N days` are deleted. |

### Examples

```bash
# Prune audit entries older than 30 days:
python manage.py prune_audit_logs --days 30
```
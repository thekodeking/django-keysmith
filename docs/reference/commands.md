# Management commands

---

## `create_token`

Create a new Keysmith API token from the command line and display the one-time raw secret.

```bash
python manage.py create_token --name NAME [options]
```

| Option | Type | Description |
| --- | --- | --- |
| `--name` | `str` | **Required.** Human-readable name for the token |
| `--user` | `str` | Username to associate this token with |
| `--description` | `str` | Optional description for the token |
| `--scopes` | `str` | Comma-separated list of permission codenames (e.g. `read,write`) |
| `--days` | `int` | Number of days until token expires |
| `--system` | flag | Create as a system token instead of a user token |

**Example:**

```bash
python manage.py create_token --name "CI Deployer" --user deployer --scopes read,write --days 90
```

---

## `revoke_token`

Revoke or permanently soft-delete (purge) an API token by its prefix.

```bash
python manage.py revoke_token PREFIX [--purge]
```

| Option | Type | Description |
| --- | --- | --- |
| `prefix` | `str` | **Required.** The token prefix (e.g. `tok_a1B2c3D4`) |
| `--purge` | flag | Soft-delete (purge) the token permanently |

**Example:**

```bash
python manage.py revoke_token tok_a1B2c3D4
python manage.py revoke_token tok_a1B2c3D4 --purge
```

---

## `list_tokens`

Display a formatted table of tokens with their name, type, user, state, and expiration.

```bash
python manage.py list_tokens [options]
```

| Option | Type | Description |
| --- | --- | --- |
| `--active` | flag | Show only active tokens (not revoked, not purged, not expired) |
| `--revoked` | flag | Show only revoked or purged tokens |
| `--expired` | flag | Show only expired tokens |
| `--user` | `str` | Filter tokens by associated username |

**Example:**

```bash
python manage.py list_tokens --active
```

---

## `prune_audit_logs`

Delete audit log rows older than a given number of days.

```bash
python manage.py prune_audit_logs [--days N]
```

| Flag | Behavior |
| --- | --- |
| `--days N` | Delete rows where `created_at < now - N days` |
| *(no flag)* | Uses `AUDIT_LOG_RETENTION_DAYS` from settings |
| Neither set | Prints warning, exits without deleting |

**Example:**

```bash
python manage.py prune_audit_logs --days 90
```\n
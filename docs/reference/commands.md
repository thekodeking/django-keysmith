# Management commands

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
```

Schedule via cron or a task runner for ongoing retention.

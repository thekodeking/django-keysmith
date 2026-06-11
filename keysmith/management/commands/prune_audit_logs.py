from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from keysmith.models.utils import get_audit_log_model
from keysmith.settings import keysmith_settings


class Command(BaseCommand):
    help = "Prune keysmith audit log entries older than N days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            help="Delete entries older than this many days.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days is None:
            days = getattr(keysmith_settings, "AUDIT_LOG_RETENTION_DAYS", None)

        if days is None:
            self.stdout.write(
                self.style.WARNING(
                    "No days specified. Please provide --days or set AUDIT_LOG_RETENTION_DAYS in settings."
                )
            )
            return

        cutoff = timezone.now() - timedelta(days=days)
        AuditLog = get_audit_log_model()
        deleted_count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {deleted_count} audit log entries older than {days} days."
            )
        )

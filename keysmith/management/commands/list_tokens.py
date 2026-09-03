from django.core.management.base import BaseCommand
from django.utils import timezone

from keysmith.models.utils import get_token_model


class Command(BaseCommand):
    help = "List Keysmith API tokens."

    def add_arguments(self, parser):
        parser.add_argument(
            "--active",
            action="store_true",
            help="Show only active tokens (not revoked, not purged, not expired).",
        )
        parser.add_argument(
            "--revoked",
            action="store_true",
            help="Show only revoked or purged tokens.",
        )
        parser.add_argument(
            "--expired",
            action="store_true",
            help="Show only expired tokens.",
        )
        parser.add_argument(
            "--user",
            type=str,
            default=None,
            help="Filter by username.",
        )

    def handle(self, *args, **options):
        Token = get_token_model()
        qs = Token.objects.select_related("user").order_by("-created_at")

        if options["user"]:
            qs = qs.filter(user__username=options["user"])

        now = timezone.now()
        if options["active"]:
            qs = qs.filter(revoked=False, purged=False).exclude(expires_at__lt=now)
        elif options["revoked"]:
            qs = qs.filter(revoked=True)
        elif options["expired"]:
            qs = qs.filter(expires_at__lt=now)

        tokens = list(qs)
        if not tokens:
            self.stdout.write("No tokens found.")
            return

        header = f"{'PREFIX':<18} {'NAME':<20} {'TYPE':<8} {'USER':<15} {'STATE':<10} {'EXPIRES AT':<20}"
        self.stdout.write(self.style.MIGRATE_HEADING(header))
        self.stdout.write("-" * len(header))

        for t in tokens:
            if t.purged:
                state = "Purged"
            elif t.revoked:
                state = "Revoked"
            elif t.is_expired:
                state = "Expired"
            else:
                state = "Active"

            username = t.user.username if t.user else "-"
            expires = str(t.expires_at.strftime("%Y-%m-%d %H:%M")) if t.expires_at else "Never"
            name = (t.name[:18] + "..") if len(t.name) > 20 else t.name

            row = f"{t.prefix:<18} {name:<20} {t.token_type:<8} {username:<15} {state:<10} {expires:<20}"
            if state == "Active":
                self.stdout.write(self.style.SUCCESS(row))
            else:
                self.stdout.write(row)

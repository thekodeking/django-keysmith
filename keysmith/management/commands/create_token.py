from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from keysmith.services.tokens import create_token


class Command(BaseCommand):
    help = "Create a new Keysmith API token and output the raw token secret."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            required=True,
            help="Human-readable name for the token.",
        )
        parser.add_argument(
            "--description",
            type=str,
            default="",
            help="Optional description for the token.",
        )
        parser.add_argument(
            "--user",
            type=str,
            default=None,
            help="Username to associate this token with.",
        )
        parser.add_argument(
            "--scopes",
            type=str,
            default=None,
            help="Comma-separated list of permission codenames (e.g. 'read,write').",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Number of days until the token expires.",
        )
        parser.add_argument(
            "--system",
            action="store_true",
            help="Create as a system token instead of a user token.",
        )

    def handle(self, *args, **options):
        user = None
        if options["user"]:
            User = get_user_model()
            try:
                user = User.objects.get(username=options["user"])
            except User.DoesNotExist as exc:
                raise CommandError(f"User with username '{options['user']}' does not exist.") from exc

        scopes = None
        if options["scopes"]:
            from django.contrib.auth.models import Permission

            scope_list = [s.strip() for s in options["scopes"].split(",") if s.strip()]
            scopes = list(Permission.objects.filter(codename__in=scope_list))

        expires_at = None
        if options["days"] is not None:
            expires_at = timezone.now() + timedelta(days=options["days"])

        token_type = "system" if options["system"] else "user"

        try:
            token, raw_token = create_token(
                name=options["name"],
                description=options["description"],
                user=user,
                scopes=scopes,
                expires_at=expires_at,
                token_type=token_type,
            )
        except Exception as exc:
            raise CommandError(f"Failed to create token: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Successfully created token '{token.name}'!"))
        self.stdout.write(f"Token ID (Prefix): {token.prefix}")
        self.stdout.write(f"Token Type:        {token.token_type}")
        self.stdout.write(f"Expires At:        {token.expires_at or 'Never'}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("Copy your secret token now. It will NOT be displayed again:"))
        self.stdout.write(self.style.SUCCESS(raw_token))
        self.stdout.write(self.style.WARNING("=" * 60))

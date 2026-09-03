from django.core.management.base import BaseCommand, CommandError

from keysmith.models.utils import get_token_model
from keysmith.services.tokens import revoke_token


class Command(BaseCommand):
    help = "Revoke or purge a Keysmith API token by its prefix."

    def add_arguments(self, parser):
        parser.add_argument(
            "prefix",
            type=str,
            help="The token prefix (e.g. 'tok_abc12345').",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Soft-delete (purge) the token permanently.",
        )

    def handle(self, *args, **options):
        prefix = options["prefix"]
        purge = options["purge"]

        Token = get_token_model()
        try:
            token = Token.objects.get(prefix=prefix)
        except Token.DoesNotExist as exc:
            raise CommandError(f"Token with prefix '{prefix}' not found.") from exc

        if token.purged:
            self.stdout.write(self.style.WARNING(f"Token '{prefix}' is already purged."))
            return

        if token.revoked and not purge:
            self.stdout.write(self.style.WARNING(f"Token '{prefix}' is already revoked."))
            return

        revoke_token(token, purge=purge)
        action_name = "purged" if purge else "revoked"
        self.stdout.write(
            self.style.SUCCESS(f"Successfully {action_name} token '{token.name}' ({prefix}).")
        )

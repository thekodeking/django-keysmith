from keysmith.models.base import AbstractToken


class Token(AbstractToken):
    """
    Default Keysmith token model.
    """

    class Meta(AbstractToken.Meta):
        db_table = "keysmith_token"

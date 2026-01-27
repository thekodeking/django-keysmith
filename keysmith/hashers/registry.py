from django.utils.module_loading import import_string
from keysmith.settings import keysmith_settings
from keysmith.hashers.base import BaseTokenHasher


def get_hasher() -> BaseTokenHasher:
    hasher_cls = import_string(keysmith_settings.HASH_BACKEND)
    return hasher_cls()

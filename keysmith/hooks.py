from django.utils.module_loading import import_string

from keysmith.settings import keysmith_settings


def load_hook(setting_name: str):
    hook_path = getattr(keysmith_settings, setting_name, None)
    if not hook_path:
        return None
    return import_string(hook_path)

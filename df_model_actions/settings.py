from django.conf import settings


class ModuleSettings:
    def __init__(self, user_settings: dict, defaults: dict):
        for key, value in defaults.items():
            value = user_settings.get(key, None) or value
            setattr(self, key, value)


DEFAULTS = {"CELERY_USE_ASYNC": False}

module_settings = ModuleSettings(getattr(settings, "DF_ACTIONS", {}), DEFAULTS)

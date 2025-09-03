from django.apps import AppConfig


class SwitchingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'energy.switching'

    def ready(self):
        import energy.switching.signals

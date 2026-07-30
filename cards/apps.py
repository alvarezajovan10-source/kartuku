from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'

    def ready(self):
        # Mendaftarkan pembersih berkas foto yatim (lihat cards/signals.py).
        from . import signals  # noqa: F401

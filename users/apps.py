from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):  # noqa: D401
        """Import signals when app is ready."""
        # Import interno para registrar receivers sin contaminar el namespace.
        import users.signals  # noqa: F401

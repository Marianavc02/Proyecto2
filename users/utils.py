from django.contrib.auth import get_user_model

User = get_user_model()


def user_display(user) -> str:
    """Siempre muestra el email (si existe) y solo cae al username si no hay email."""
    return user.email or user.get_username()

from .settings import *  # noqa

# Fuerza una base de datos local y efímera para pruebas.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:", "SERIALIZE": False},
    }
}

# Acelera tests (hashing más rápido, menos validaciones estrictas si se desea)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Evita ruido en tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

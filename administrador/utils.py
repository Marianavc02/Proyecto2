from django.utils import timezone

from .models import CampaniaConfig


def obtener_config():
    """
    Retorna la única configuración (crea una por defecto si no existe).
    """
    cfg, _ = CampaniaConfig.objects.get_or_create(
        pk=1,
        defaults={
            # Por defecto: hoy + 1 hora a hoy + 2 horas
            "inicio": timezone.now() + timezone.timedelta(hours=1),
            "fin": timezone.now() + timezone.timedelta(hours=2),
            "habilitada": True,
        },
    )
    return cfg


def puede_ver_usuario(user, ahora=None):
    """
    True si el usuario puede usar la plataforma.
    - Admin (is_staff) siempre puede.
    - Usuarios normales: solo si campaña activa.
    """
    if user.is_authenticated and user.is_staff:
        return True
    cfg = obtener_config()
    return cfg.esta_activa(ahora=ahora or timezone.now())

from django.utils import timezone

from .models import CampaniaConfig


def obtener_config():
    """
    Retorna la campaña habilitada más reciente (o None si no existe).
    """
    cfg = CampaniaConfig.objects.filter(habilitada=True).order_by("-id").first()
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

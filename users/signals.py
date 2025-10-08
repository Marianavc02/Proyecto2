from allauth.account.signals import user_logged_in
from django.conf import settings
from django.dispatch import receiver

from empleados.models import Empleado


@receiver(user_logged_in)
def verificar_empleado(sender, request, user, **kwargs):
    """Desactiva usuarios cuyo email no esté en Empleado, solo si la política lo exige.

    Controlado por setting SBD_REQUIRE_EMPLEADO (True por defecto). Si se pone
    en False (por ejemplo en desarrollo), se permite el login sin restricción.
    """
    require = getattr(settings, "SBD_REQUIRE_EMPLEADO", True)
    if not require:
        # Si la política no exige validación y el usuario quedó inactivo de antes, lo reactivamos.
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])
        return
    email = (user.email or "").lower()
    if not email:
        return
    if not Empleado.objects.filter(sbd_email=email).exists():
        user.is_active = False
        user.save(update_fields=["is_active"])
        from django.contrib.auth import logout

        logout(request)

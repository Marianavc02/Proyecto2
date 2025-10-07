from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from django.contrib.auth.models import User
from empleados.models import Empleado

@receiver(user_logged_in)
def verificar_empleado(sender, request, user, **kwargs):
    email = user.email.lower()
    if not Empleado.objects.filter(sbd_email=email).exists():
        # Si el usuario no está autorizado, desactívalo y ciérralo
        user.is_active = False
        user.save()
        from django.contrib.auth import logout
        logout(request)

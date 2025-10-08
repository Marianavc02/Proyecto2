from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def perfil(request):
    """Vista de perfil simple."""
    return render(request, "users/perfil.html")


def logout_view(request):
    """Cierra sesión y redirige al home."""
    logout(request)
    return redirect("/")


# Callback de Microsoft ahora lo maneja django-allauth internamente.

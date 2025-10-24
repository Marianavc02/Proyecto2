from django.shortcuts import render


def home(request):
    # Si el usuario NO está autenticado, muestra la fachada del login
    if not request.user.is_authenticated:
        return render(request, "login_fachada.html")
    return render(request, "home.html")

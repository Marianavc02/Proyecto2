from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@login_required
def perfil(request):
    return render(request, 'users/perfil.html')

def logout_view(request):
    logout(request)
    return redirect('/')


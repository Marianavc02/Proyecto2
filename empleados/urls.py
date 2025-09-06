from django.urls import path
from . import views

urlpatterns = [
    path("", views.lista_empleados, name="lista_empleados"),
    path("importar/", views.importar_empleados, name="importar_empleados"),
]

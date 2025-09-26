from django.urls import path

from . import views

app_name = "administrador"

urlpatterns = [
    path("fechas/", views.programar_fechas, name="programar_fechas"),
    path("estado/", views.estado_campania, name="estado_campania"),
    path("reporte-pedidos/", views.reporte_pedidos, name="reporte_pedidos"),
]

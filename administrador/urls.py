from django.urls import path

from . import views

app_name = "administrador"

urlpatterns = [
    path("base-admin/", views.base_admin, name="base_admin"),
    path("fechas/", views.programar_fechas, name="programar_fechas"),
    path("estado/", views.estado_campania, name="estado_campania"),
    path("reporte-pedidos/", views.reporte_pedidos, name="reporte_pedidos"),
    path("exportar_reporte_excel/", views.exportar_reporte_excel, name="exportar_reporte_excel"),
    path("empleados-reporte/", views.lista_empleados_reporte, name="lista_empleados_reporte"),
    path("empleados/<int:empleado_id>/reporte/", views.reporte_pedidos_empleado, name="reporte_pedidos_empleado"),
]

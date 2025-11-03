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
    path(
        "reporte-empleado/<int:empleado_id>/exportar/",
        views.exportar_reporte_empleado_excel,
        name="exportar_reporte_empleado_excel",
    ),
    path("empleados/<int:empleado_id>/reporte/", views.reporte_pedidos_empleado, name="reporte_pedidos_empleado"),
    path(
        "pedido/<int:pedido_id>/resumen/",
        views.generar_resumen_pedido,
        name="generar_resumen_pedido",
    ),
    path("modificar-pedido/<int:pedido_id>/", views.modificar_pedido, name="modificar_pedido"),
    path("acta-entrega/<int:pedido_id>/", views.generar_acta_entrega, name="generar_acta_entrega"),
    path("politica/", views.editar_politica_compra, name="editar_politica_compra"),
    path("dismiss-policy/", views.dismiss_policy, name="dismiss_policy"),
    path("mas-info/", views.masinfo_page, name="masinfo"),
    path("mas-info/editar/", views.editar_masinfo, name="editar_masinfo"),
    path("empleados-reporte/pdf/", views.exportar_resumen_empleados_pdf, name="exportar_resumen_empleados_pdf"),
    path("empleados-reporte/actas-zip/", views.exportar_actas_filtradas_zip, name="exportar_actas_filtradas_zip"),
]

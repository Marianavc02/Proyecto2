# urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("cargar-excel/", views.cargar_excel, name="cargar_excel"),
    path("lista-productos/", views.lista_productos, name="lista_productos"),
    path("cargar-imagen/", views.cargar_imagen, name="cargar_imagen"),
    path("actualizar-stock-minimo/", views.actualizar_stock_minimo, name="actualizar_stock_minimo"),
    path("empresa/<str:empresa>/", views.productos_por_empresa, name="productos_por_empresa"),
    path("producto/<int:pk>/", views.detalle_producto, name="detalle_producto"),
    path("carrito/", views.carrito_ver, name="carrito_ver"),
    path("carrito/agregar/<str:sku>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/eliminar/<str:sku>/", views.carrito_eliminar, name="carrito_eliminar"),
    path("buscar/", views.buscar_productos, name="buscar_productos"),
    path("enviar-pedido/", views.enviar_pedido, name="enviar_pedido"),
    path("lista-pedidos/", views.lista_pedidos, name="lista_pedidos"),
]

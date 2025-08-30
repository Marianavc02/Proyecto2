# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('cargar-excel/', views.cargar_excel, name='cargar_excel'),
    path('lista-productos/', views.lista_productos, name='lista_productos'),
    path('cargar-imagen/', views.cargar_imagen, name='cargar_imagen'),
    path('empresa/<str:empresa>/', views.productos_por_empresa, name='productos_por_empresa'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
]
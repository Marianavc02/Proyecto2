# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('cargar-excel/', views.cargar_excel, name='cargar_excel'),
    path('productos/', views.lista_productos, name='lista_productos'),
    path('cargar-imagen/', views.cargar_imagen, name='cargar_imagen'),
]
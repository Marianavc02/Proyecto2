from django.contrib import admin
from .models import Empleado

# Registramos el modelo en el admin
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'preferred_name', 'sbd_email')  # columnas visibles en el listado
    search_fields = ('preferred_name', 'sbd_email')       # barra de búsqueda
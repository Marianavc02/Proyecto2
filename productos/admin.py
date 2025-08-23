from django.contrib import admin
from .models import Producto, ProductoImagen

# Para mostrar las imágenes relacionadas dentro del producto
class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1  # Cuántas filas vacías mostrar para agregar nuevas imágenes
    readonly_fields = ('imagen_preview',)  # Opcional: vista previa de la imagen
    fields = ('imagen', 'imagen_preview')  

    # Método para mostrar una miniatura de la imagen
    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 100px; height:auto;" />', obj.imagen.url)
        return "-"
    imagen_preview.short_description = 'Vista previa'

# Admin de Producto
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'descripcion','sbu', 'categoria', 'precio_sin_iva')  # Ajusta según tus campos
    inlines = [ProductoImagenInline]

# Admin de ProductoImagen (opcional, si quieres verlo separado también)
@admin.register(ProductoImagen)
class ProductoImagenAdmin(admin.ModelAdmin):
    list_display = ('producto', 'fecha_creacion', 'imagen')

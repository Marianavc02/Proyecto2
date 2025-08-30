# models.py
from .utils import clasificar_empresa
from django.db import models
import os

def image_upload_path(instance, filename):
    # Guardar imágenes en: media/productos/SKU/filename
    return os.path.join('productos', instance.sku, filename)

class Producto(models.Model):
    sku = models.CharField("Referencia", max_length=100, unique=True)  # antes era 'codigo_barras'/'referencia'
    descripcion = models.TextField("Descripción")
    sbu = models.CharField("SBU", max_length=100, blank=True, null=True)
    categoria = models.CharField("Categoría", max_length=100, blank=True, null=True)
    precio_sin_iva = models.DecimalField("Precio antes de IVA", max_digits=10, decimal_places=2, null=True, blank=True)
    empresa = models.CharField("Empresa", max_length=50, blank=True, null=True)
#save para que siempre que se guarde en la base de datos se le ponga empresa
    def save(self, *args, **kwargs):
        self.empresa = clasificar_empresa(self.sku)
        super().save(*args, **kwargs)

def image_upload_path(instance, filename):
    return f"productos/{instance.producto.sku}/{filename}"  # usa el SKU del producto

class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to=image_upload_path)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen de {self.producto.sku}"


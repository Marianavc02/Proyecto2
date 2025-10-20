from django.contrib.auth.models import User
from django.db import models

from .utils import clasificar_empresa


def image_upload_path(instance, filename):
    return f"productos/{instance.producto.sku}/{filename}"  # usa el SKU del producto


class Producto(models.Model):

    sku = models.CharField("Referencia", max_length=100, unique=True)
    descripcion = models.TextField("Descripción")
    sbu = models.CharField("SBU", max_length=100, blank=True, null=True)
    categoria = models.CharField("Categoría", max_length=100, blank=True, null=True)
    precio_sin_iva = models.DecimalField("Precio antes de IVA", max_digits=10, decimal_places=2, null=True, blank=True)
    empresa = models.CharField("Empresa", max_length=50, blank=True, null=True)
    # Nuevo: stock actual y mínimo de pedido
    stock = models.PositiveIntegerField("Stock actual", default=0)
    minimo_pedido = models.PositiveIntegerField(
        "Mínimo para pedido", default=1, help_text="Cantidad mínima para que el producto sea factible de enviar."
    )
    # save para que siempre que se guarde en la base de datos se le ponga empresa
    # === IA ===
    descripcion_ai = models.TextField("Descripción IA", null=True, blank=True)
    descripcion_ai_updated = models.DateTimeField("Descripción IA actualizada", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.empresa = clasificar_empresa(self.sku)
        super().save(*args, **kwargs)


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="imagenes")
    imagen = models.ImageField(upload_to=image_upload_path)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen de {self.producto.sku}"


class Pedido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empleado = models.ForeignKey("empleados.Empleado", on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.empleado or self.usuario}"

    @property
    def total(self):
        """Calcula el total sumando todos los items del pedido."""
        return sum(item.producto.precio_sin_iva * item.cantidad for item in self.items.all())


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.producto.descripcion} x {self.cantidad}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

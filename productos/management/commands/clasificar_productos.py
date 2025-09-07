# productos/management/commands/clasificar_productos.py
from django.core.management.base import BaseCommand

from productos.models import Producto
from productos.utils import clasificar_empresa


class Command(BaseCommand):
    help = "Clasifica los productos existentes en base al SKU"

    def handle(self, *args, **kwargs):
        productos = Producto.objects.all()
        total = productos.count()
        self.stdout.write(self.style.NOTICE(f"Clasificando {total} productos..."))

        for producto in productos:
            nueva_empresa = clasificar_empresa(producto.sku)
            if producto.empresa != nueva_empresa:
                producto.empresa = nueva_empresa
                producto.save(update_fields=["empresa"])
                self.stdout.write(f"{producto.sku} -> {nueva_empresa}")

        self.stdout.write(self.style.SUCCESS("Clasificación completada."))

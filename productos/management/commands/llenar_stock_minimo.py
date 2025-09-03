from django.core.management.base import BaseCommand
from productos.models import Producto
import random

class Command(BaseCommand):
    help = 'Llena los campos stock y minimo_pedido para todos los productos existentes.'

    def handle(self, *args, **kwargs):
        productos = Producto.objects.all()
        for producto in productos:
            # Stock aleatorio entre 10 y 500 si está vacío
            if producto.stock == 0:
                producto.stock = random.randint(10, 500)
            # Mínimo pedido: 10% del stock, al menos 1
            producto.minimo_pedido = max(1, int(producto.stock * 0.1))
            producto.save()
        self.stdout.write(self.style.SUCCESS('Campos stock y minimo_pedido actualizados para todos los productos.'))

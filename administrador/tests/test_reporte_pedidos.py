import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem, Producto


@pytest.mark.django_db
class TestReportePedidosView:

    def test_sin_filtros(self, client):
        response = client.get(reverse("administrador:reporte_pedidos"))
        assert response.status_code == 200
        assert "reporte" in response.context

    def test_con_filtro_query(self, client):
        # Crear usuario y empleado
        user = User.objects.create(username="testuser2")
        empleado = Empleado.objects.create(preferred_name="María Gómez", sbd_email="maria.gomez@sbd.com")

        # Crear producto
        producto = Producto.objects.create(sku="XYZ999", descripcion="Producto filtrado", sbu="SBU2")

        # Crear pedido asociado a usuario y empleado
        pedido = Pedido.objects.create(usuario=user, empleado=empleado)

        # Crear item del pedido
        PedidoItem.objects.create(pedido=pedido, producto=producto, cantidad=5)

        # Petición con filtro por SKU
        response = client.get(reverse("administrador:reporte_pedidos") + "?query=XYZ999")
        assert response.status_code == 200
        assert "Producto filtrado" in response.content.decode()

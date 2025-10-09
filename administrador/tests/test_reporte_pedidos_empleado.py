from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem, Producto


@pytest.mark.django_db
class TestReportePedidosEmpleadoView:
    def test_reporte_empleado_renderiza(self, client):
        # Crear usuario
        user = User.objects.create(username="cliente")
        # Crear empleado
        empleado = Empleado.objects.create(preferred_name="María Lopez", sbd_email="maria2.gomez@sbd.com")
        # Crear producto
        producto = Producto.objects.create(
            sku="ZXY", descripcion="Producto X", precio_sin_iva=Decimal("10.00")  # usar Decimal
        )
        # Crear pedido
        pedido = Pedido.objects.create(usuario=user, empleado=empleado)
        # Crear item del pedido
        PedidoItem.objects.create(pedido=pedido, producto=producto, cantidad=3)
        # Acceder a la URL del reporte
        url = reverse("administrador:reporte_pedidos_empleado", args=[empleado.id])
        response = client.get(url)
        # Comprobar status y contexto
        assert response.status_code == 200
        assert "empleado" in response.context
        assert "total_general" in response.context
        # Comprobar que el total se calcula correctamente
        total_esperado = producto.precio_sin_iva * 3
        assert response.context["total_general"] == total_esperado

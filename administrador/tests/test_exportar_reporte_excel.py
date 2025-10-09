import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem, Producto


@pytest.mark.django_db
class TestExportarReporteExcelView:

    def test_exporta_archivo_excel(self, client):
        # Crear usuario y empleado
        user = User.objects.create(username="usuario")
        empleado = Empleado.objects.create(preferred_name="Empleado Test", sbd_email="empleado@test.com")

        # Crear producto
        producto = Producto.objects.create(sku="ABC123", descripcion="Desc test", sbu="X")

        # Crear pedido asociado a usuario y empleado
        pedido = Pedido.objects.create(usuario=user, empleado=empleado)

        # Crear item del pedido
        PedidoItem.objects.create(pedido=pedido, producto=producto, cantidad=2)

        # Llamada a la vista de exportación
        response = client.get(reverse("administrador:exportar_reporte_excel"))

        # Verificar que se genera un archivo Excel
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

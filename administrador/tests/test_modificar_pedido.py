import pytest
from django.urls import reverse

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem, Producto
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestModificarPedido:
    def _crear_datos_basicos(self):
        """Crea usuario staff, empleado, pedido y dos productos con items."""
        admin = User.objects.create_user(username="admin", password="1234", is_staff=True)
        empleado = Empleado.objects.create(preferred_name="Ana", sbd_email="ana@example.com")

        p1 = Producto.objects.create(sku="SKU-1", descripcion="Prod 1", precio_sin_iva=10)
        p2 = Producto.objects.create(sku="SKU-2", descripcion="Prod 2", precio_sin_iva=20)

        pedido = Pedido.objects.create(usuario=admin, empleado=empleado)
        item1 = PedidoItem.objects.create(pedido=pedido, producto=p1, cantidad=1)
        item2 = PedidoItem.objects.create(pedido=pedido, producto=p2, cantidad=2)
        return admin, empleado, pedido, item1, item2

    def test_admin_puede_eliminar_item_de_pedido(self, client):
        # Arrange
        admin, _empleado, pedido, item1, item2 = self._crear_datos_basicos()
        client.force_login(admin)
        url = reverse("administrador:modificar_pedido", args=[pedido.id])

        # Act: eliminar el item1
        response = client.post(url, {"item_id": item1.id})

        # Assert: redirige a la misma vista y el item1 ya no existe
        assert response.status_code == 302
        assert response.headers["Location"].endswith(url)
        assert not PedidoItem.objects.filter(id=item1.id).exists()
        # El otro item sigue existiendo
        assert PedidoItem.objects.filter(id=item2.id, pedido=pedido).count() == 1

    def test_404_si_item_no_pertenece_al_pedido(self, client):
        # Arrange: dos pedidos, el item pertenece al segundo
        admin = User.objects.create_user(username="admin2", password="1234", is_staff=True)
        client.force_login(admin)

        empleado = Empleado.objects.create(preferred_name="Ben", sbd_email="ben@example.com")
        p = Producto.objects.create(sku="SKU-3", descripcion="Prod 3", precio_sin_iva=30)

        pedido_a = Pedido.objects.create(usuario=admin, empleado=empleado)
        pedido_b = Pedido.objects.create(usuario=admin, empleado=empleado)

        item_b = PedidoItem.objects.create(pedido=pedido_b, producto=p, cantidad=1)

        url = reverse("administrador:modificar_pedido", args=[pedido_a.id])

        # Act: intento eliminar item de otro pedido
        response = client.post(url, {"item_id": item_b.id})

        # Assert
        assert response.status_code == 404
        # Y no se borró
        assert PedidoItem.objects.filter(id=item_b.id, pedido=pedido_b).exists()

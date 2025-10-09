from decimal import Decimal

import pytest
from django.urls import reverse

from productos.models import Producto


@pytest.mark.django_db
def test_lista_productos(client):
    # Crear productos de prueba
    Producto.objects.create(sku="SKU1", descripcion="Producto 1", precio_sin_iva=Decimal("10.00"))
    Producto.objects.create(sku="SKU2", descripcion="Producto 2", precio_sin_iva=Decimal("20.00"))

    url = reverse("lista_productos")
    response = client.get(url)
    assert response.status_code == 200
    assert "Producto 1" in response.content.decode()
    assert "Producto 2" in response.content.decode()

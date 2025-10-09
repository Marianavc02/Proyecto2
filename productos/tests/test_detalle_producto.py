from decimal import Decimal

import pytest
from django.urls import reverse

from productos.models import Producto


@pytest.mark.django_db
def test_detalle_producto(client):
    p = Producto.objects.create(sku="SKU1", descripcion="Producto 1", minimo_pedido=1, precio_sin_iva=Decimal("10.00"))

    url = reverse("detalle_producto", args=[p.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert "Producto 1" in response.content.decode()

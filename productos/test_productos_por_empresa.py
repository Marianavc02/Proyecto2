"""
import pytest
from django.urls import reverse

from productos.models import Producto


@pytest.mark.django_db
def test_filtrar_productos_por_marca(client, monkeypatch):
    # Sobrescribimos la función clasificar_empresa para que no modifique nada
    monkeypatch.setattr("productos.models.clasificar_empresa", lambda sku: "MarcaA")

    # Crear productos de prueba
    producto1 = Producto.objects.create(
        sku="SKU1", descripcion="Producto 1", sbu="SBU1", categoria="Cat1", precio_sin_iva=10
    )
    producto2 = Producto.objects.create(
        sku="SKU2", descripcion="Producto 2", sbu="SBU2", categoria="Cat2", precio_sin_iva=20
    )

    url = reverse("productos_por_empresa", args=["MarcaA"])
    response = client.get(url, {"marca": "MarcaA"})

    assert response.status_code == 200

    productos = response.context["productos"]
    assert len(productos) == 2
    for p in productos:
        assert "MarcaA" in p.empresa
"""

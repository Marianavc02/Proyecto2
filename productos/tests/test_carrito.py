# productos/tests/test_carrito.py
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from productos.models import Producto

pytestmark = pytest.mark.django_db


def crear_producto(sku, precio="100.00", minimo=1, **extras):
    """
    Helper para crear un Producto mínimo para los tests.
    Ajusta los campos si tu modelo exige otros obligatorios.
    """
    return Producto.objects.create(
        sku=sku,
        descripcion=f"Producto {sku}",
        precio_sin_iva=Decimal(precio),
        minimo_pedido=minimo,
        categoria=extras.get("categoria", ""),
        empresa=extras.get("empresa", ""),
    )


# -------------------
# RF_12: Agregar
# -------------------


def test_agregar_requiere_post(client):
    # GET debe redirigir a carrito_ver (tu vista lo hace)
    url = reverse("carrito_agregar", args=["SKU1"])
    resp = client.get(url, follow=True)
    assert resp.redirect_chain  # hubo redirect
    assert resp.resolver_match.view_name == "carrito_ver"


def test_agregar_un_producto_ok(client):
    crear_producto("SKU1")
    url = reverse("carrito_agregar", args=["SKU1"])

    resp = client.post(url, follow=True)
    # Debe redirigir a carrito_ver y dejar mensaje de éxito
    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("agregado" in m.lower() for m in msgs)

    # Ver el carrito y validar count=1
    ver = client.get(reverse("carrito_ver"))
    assert ver.context["count"] == 1


def test_agregar_no_permite_repetidos(client):
    crear_producto("SKU1")
    url = reverse("carrito_agregar", args=["SKU1"])

    client.post(url, follow=True)  # primera vez
    resp = client.post(url, follow=True)  # repetido

    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("ya está en tu carrito" in m.lower() for m in msgs)

    ver = client.get(reverse("carrito_ver"))
    assert ver.context["count"] == 1  # sigue habiendo solo 1


def test_agregar_hasta_maximo_cinco_y_sexto_rechazado(client):
    # Crea 6 productos
    for i in range(1, 7):
        crear_producto(f"SKU{i}")

    # Agrega 5 distintos
    for i in range(1, 6):
        client.post(reverse("carrito_agregar", args=[f"SKU{i}"]), follow=True)

    # Intento 6º debe advertir y NO aumentar el count
    resp = client.post(reverse("carrito_agregar", args=["SKU6"]), follow=True)
    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("no puedes agregar más de 5" in m.lower() for m in msgs)

    ver = client.get(reverse("carrito_ver"))
    assert ver.context["count"] == 5


def test_agregar_producto_inexistente_muestra_error(client):
    # No se crea el producto
    resp = client.post(reverse("carrito_agregar", args=["NOEXISTE"]), follow=True)
    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("no encontrado" in m.lower() for m in msgs)

    ver = client.get(reverse("carrito_ver"))
    assert ver.context["count"] == 0


# -------------------
# RF_13: Eliminar
# -------------------


def test_eliminar_existente_y_mensaje_vacio(client):
    crear_producto("SKU1")
    client.post(reverse("carrito_agregar", args=["SKU1"]), follow=True)

    resp = client.post(reverse("carrito_eliminar", args=["SKU1"]), follow=True)
    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("carrito vacío" in m.lower() for m in msgs)

    ver = client.get(reverse("carrito_ver"))
    assert ver.context["count"] == 0


def test_eliminar_no_existente_mensaje_warning(client):
    # Carrito vacío, intento eliminar SKU que no está
    resp = client.post(reverse("carrito_eliminar", args=["SKU9"]), follow=True)
    msgs = [m.message for m in get_messages(resp.wsgi_request)]
    assert any("no estaba en tu carrito" in m.lower() for m in msgs)


# -------------------
# RF_14: Ver carrito
# -------------------


def test_ver_carrito_calcula_total_y_productos_no_cumplen_minimo(client):
    # SKU1 cumple mínimo=1, SKU2 no cumple mínimo=3
    crear_producto("SKU1", precio="10.00", minimo=1)
    crear_producto("SKU2", precio="20.00", minimo=3)

    client.post(reverse("carrito_agregar", args=["SKU1"]), follow=True)
    client.post(reverse("carrito_agregar", args=["SKU2"]), follow=True)

    resp = client.get(reverse("carrito_ver"))
    ctx = resp.context

    # total = 10 + 20 (una unidad por producto)
    assert ctx["total"] == Decimal("30.00")
    assert ctx["count"] == 2

    # productos_no_cumplen debe contener SKU2 (mínimo 3 y tenemos 1)
    no_cumplen = ctx["productos_no_cumplen"]
    assert any(it["sku"] == "SKU2" and it["faltan"] == 2 for it in no_cumplen)

    # Renderiza la plantilla del carrito
    templates = [t.name for t in resp.templates if t.name]
    assert "productos/carrito.html" in templates

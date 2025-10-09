# productos/tests/test_cargar_excel_productos.py
import io

import pandas as pd
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from productos.models import Producto


@pytest.mark.django_db
def test_cargar_excel(client):
    # Crear un DataFrame para el Excel
    df1 = pd.DataFrame(
        {
            "SKU": ["SKU1", "SKU2"],
            "DESCRICIÓN": ["Producto 1", "Producto 2"],
            "SBU": ["SBU1", "SBU2"],
            "CATEGORÍA": ["Cat1", "Cat2"],
            "PRECIO ANTES DE IVA": [10, 20],
        }
    )

    df2 = pd.DataFrame(
        {
            "SKU": ["SKU1", "SKU2"],
            "UND EMPAQUE": [1, 2],
        }
    )

    # Crear archivos Excel en memoria
    excel1 = io.BytesIO()
    with pd.ExcelWriter(excel1, engine="openpyxl") as writer:
        df1.to_excel(writer, index=False)
    excel1.seek(0)

    excel2 = io.BytesIO()
    with pd.ExcelWriter(excel2, engine="openpyxl") as writer:
        df2.to_excel(writer, index=False)
    excel2.seek(0)

    # Crear objetos SimpleUploadedFile
    file1 = SimpleUploadedFile(
        "archivo1.xlsx", excel1.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    excel1.seek(0)
    file2 = SimpleUploadedFile(
        "archivo2.xlsx", excel2.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Hacer POST a la vista
    url = reverse("cargar_excel")
    response = client.post(url, {"archivo1": file1, "archivo2": file2})

    # Verificar redirección
    assert response.status_code == 302
    assert response.url == reverse("lista_productos")

    # Verificar que se crearon los productos
    productos = Producto.objects.all()
    assert productos.count() == 2
    assert productos.filter(sku="SKU1").exists()
    assert productos.filter(sku="SKU2").exists()

import io

import pandas as pd
import pytest
from django.urls import reverse

from empleados.models import Empleado


@pytest.mark.django_db
def test_importar_empleados(client):
    # Crear un Excel en memoria
    df = pd.DataFrame(
        {
            "ID": [1, 2],
            "Preferred Name": ["Ana Perez", "Juan Gomez"],
            "SBD Email": ["ana.perez@sbd.com", "juan.gomez@sbd.com"],
        }
    )

    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_file.seek(0)  # Resetear el puntero

    # Subir archivo usando POST
    url = reverse("importar_empleados")
    response = client.post(url, {"file": excel_file})

    # Redirección después de importar
    assert response.status_code == 302
    assert response.url == reverse("lista_empleados")

    # Verificar que se crearon los empleados
    empleados = Empleado.objects.all()
    assert empleados.count() == 2
    assert empleados.filter(preferred_name="Ana Perez").exists()
    assert empleados.filter(preferred_name="Juan Gomez").exists()

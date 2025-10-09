import pytest
from django.urls import reverse

from empleados.models import Empleado


@pytest.mark.django_db
class TestListaEmpleadosReporteView:
    def test_lista_empleados_renderiza(self, client):
        Empleado.objects.create(preferred_name="María Gómez", sbd_email="maria.gomez@sbd.com")
        url = reverse("administrador:lista_empleados_reporte")
        response = client.get(url)
        assert response.status_code == 200
        assert "empleados" in response.context
        assert len(response.context["empleados"]) >= 1

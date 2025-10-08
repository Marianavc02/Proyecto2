# administrador/tests/test_programar_fechas.py
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from administrador.models import CampaniaConfig

DT_FMT = "%Y-%m-%dT%H:%M"


def _reset_and_make_cfg(inicio, fin, habilitada=False):
    """Deja una sola CampaniaConfig para evitar interferencias."""
    CampaniaConfig.objects.all().delete()
    return CampaniaConfig.objects.create(inicio=inicio, fin=fin, habilitada=habilitada)


@pytest.mark.django_db
def test_get_muestra_form_con_config(client):
    """GET debe renderizar el formulario con la configuración actual."""
    cfg = _reset_and_make_cfg(
        inicio=timezone.now(),
        fin=timezone.now() + timedelta(days=1),
        habilitada=False,
    )
    url = reverse("administrador:programar_fechas")
    resp = client.get(url)

    assert resp.status_code == 200
    assert "form" in resp.context
    assert "cfg" in resp.context
    assert resp.context["cfg"].pk == cfg.pk


@pytest.mark.django_db
def test_post_eliminar_resetea_fechas_y_desactiva(client, monkeypatch):
    """
    Si viene 'eliminar' en el POST: pone inicio/fin = ahora y habilitada=False.
    """
    fijo = timezone.now()
    monkeypatch.setattr("django.utils.timezone.now", lambda: fijo)

    _reset_and_make_cfg(
        inicio=fijo - timedelta(days=10),
        fin=fijo + timedelta(days=10),
        habilitada=True,
    )

    url = reverse("administrador:programar_fechas")
    resp = client.post(url, data={"eliminar": "1"}, follow=True)

    # si redirige o no, al menos renderiza y actualiza:
    assert resp.status_code == 200

    cfg = CampaniaConfig.objects.first()
    # tolerancia amplia (≤ 5s) por si el render toma unos ms
    assert abs((cfg.inicio - fijo).total_seconds()) <= 5
    assert abs((cfg.fin - fijo).total_seconds()) <= 5
    assert cfg.habilitada is False

    msgs = list(resp.context["messages"])
    assert any("Campaña eliminada. No hay campaña programada." in str(m) for m in msgs)


@pytest.mark.django_db
def test_post_invalido_no_guarda_y_no_redirige(client):
    """
    Si el form es inválido (fin < inicio), no debe redirigir ni guardar cambios.
    """
    cfg = _reset_and_make_cfg(
        inicio=timezone.now(),
        fin=timezone.now() + timedelta(days=1),
        habilitada=False,
    )

    inicio = (timezone.now() + timedelta(days=5)).strftime(DT_FMT)
    fin = (timezone.now() + timedelta(days=3)).strftime(DT_FMT)

    url = reverse("administrador:programar_fechas")
    resp = client.post(
        url,
        data={"inicio": inicio, "fin": fin, "habilitada": "on"},
        follow=False,  # inválido => re-render del form (200), no redirect
    )

    assert resp.status_code == 200
    cfg.refresh_from_db()
    assert cfg.inicio < cfg.fin
    assert "form" in resp.context
    assert resp.context["form"].errors

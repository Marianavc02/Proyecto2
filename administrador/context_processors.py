# administrador/context_processors.py
from __future__ import annotations

from django.http import HttpRequest
from django.utils import timezone

from .models import CampaniaConfig  # <-- importa el nombre correcto
from .models import PoliticaCompra


def campania_nav(request):
    """
    Expone en todas las plantillas:
      - campania_cfg: el objeto (o None)
      - nav_campania: fechas en ISO para el contador del header
    """
    cfg = CampaniaConfig.objects.order_by("-id").first()

    if not cfg or not cfg.habilitada:
        return {
            "campania_cfg": None,
            "nav_campania": {
                "has": False,
                "inicio_iso": "",
                "fin_iso": "",
            },
        }

    tz = timezone.get_current_timezone()
    inicio_iso = cfg.inicio.astimezone(tz).isoformat()
    fin_iso = cfg.fin.astimezone(tz).isoformat()

    return {
        "campania_cfg": cfg,
        "nav_campania": {
            "has": True,
            "inicio_iso": inicio_iso,
            "fin_iso": fin_iso,
        },
    }


def _policy_session_key(p: PoliticaCompra) -> str:
    # Identificador único para mostrar la política solo una vez por versión
    return f"policy_shown_{p.id}_{int(p.actualizado.timestamp())}"


def politica_compra_ctx(request: HttpRequest) -> dict:
    """
    Inyecta en el contexto:
      - politica_compra: última política activa
      - must_show_policy: True si debe mostrarse el modal
    """
    ctx = {"politica_compra": None, "must_show_policy": False}

    try:
        politica = PoliticaCompra.objects.filter(activo=True).order_by("-actualizado").first()
    except Exception:
        politica = None

    if not politica:
        return ctx

    ctx["politica_compra"] = politica

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or user.is_staff:
        # No mostrar a anónimos o admins
        return ctx
    key = _policy_session_key(politica)
    already_shown = request.session.get(key, False)
    ctx["must_show_policy"] = not already_shown
    return ctx

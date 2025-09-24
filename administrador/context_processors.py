# administrador/context_processors.py
from django.utils import timezone

from .models import CampaniaConfig  # <-- importa el nombre correcto


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

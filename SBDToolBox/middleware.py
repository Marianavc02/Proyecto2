from django.shortcuts import render
from django.utils import timezone

from administrador.models import CampaniaConfig


class CampaniaMiddleware:
    """Reglas:
    - No autenticados -> pasan (login/portada).
    - is_staff -> pasan siempre.
    - Libres: /admin, /accounts, /static/, /media/, /favicon.ico
    - Autenticados NO admin -> exigir campaña activa.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _path_libre(self, path: str) -> bool:
        libres = ("/admin", "/accounts", "/static/", "/media/", "/favicon.ico")
        return path.startswith(libres)

    def __call__(self, request):
        path = request.path

        # 1) No autenticados -> dejan pasar (para ver login/portada)
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 2) Rutas libres (incluye /media/ para PDFs, imágenes, etc.)
        if self._path_libre(path):
            return self.get_response(request)

        # 3) Admins pasan siempre
        if request.user.is_staff:
            return self.get_response(request)

        # 4) Usuario autenticado NO admin -> exigir campaña activa
        ahora = timezone.now()
        campania = (
            CampaniaConfig.objects.filter(habilitada=True, inicio__lte=ahora, fin__gte=ahora)
            .order_by("-inicio")
            .first()
        )
        if campania:
            return self.get_response(request)

        # 5) Sin campaña -> página de bloqueo + banner si existe
        banner_url = None
        cfg = CampaniaConfig.objects.order_by("-actualizado").first()
        if cfg and cfg.banner:
            try:
                banner_url = cfg.banner.url
            except Exception:
                banner_url = None

        return render(
            request,
            "pagina_no_disponible.html",
            {"banner_url": banner_url},
            status=503,
        )

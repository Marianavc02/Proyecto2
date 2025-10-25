from django.shortcuts import render
from django.utils import timezone

from administrador.models import CampaniaConfig


class CampaniaMiddleware:
    """Reglas:
    - Usuarios NO autenticados -> pasan siempre (ven login/portada).
    - is_staff -> pasan siempre.
    - Se dejan libres /admin, /accounts, /static, /media.
    - Autenticados NO admin -> si no hay campaña activa, mostrar página bloqueada.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _path_libre(self, path: str) -> bool:
        libres = ("/admin", "/accounts", "/static", "/media")
        return path.startswith(libres)

    def __call__(self, request):
        path = request.path

        # 1) SIEMPRE dejar pasar a no autenticados (que puedan llegar a login, portada, etc.)
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 2) Rutas libres (por si un autenticado navega a ellas)
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

        # 5) Sin campaña -> banner si existe
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

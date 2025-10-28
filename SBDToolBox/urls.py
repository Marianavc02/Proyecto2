from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from SBDToolBox.views import home
from SBDToolBox.views_media import serve_media_noframeblock

urlpatterns = [
    path("admin/", admin.site.urls),
    path("empleados/", include("empleados.urls")),
    path("productos/", include("productos.urls")),
    path("", home, name="home"),
    path("administrador/", include("administrador.urls")),
    path("accounts/", include("allauth.urls")),
    path("", include("users.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve_media_noframeblock),
    ]

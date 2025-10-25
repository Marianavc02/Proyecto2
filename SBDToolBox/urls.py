from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from SBDToolBox.views import home

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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

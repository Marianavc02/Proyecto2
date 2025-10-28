from django.db import models
from django.utils import timezone


class CampaniaConfig(models.Model):
    """
    Configuración de la campaña. Normalmente habrá SOLO un registro (pk=1).
    """

    inicio = models.DateTimeField(help_text="Fecha y hora de inicio (UTC por defecto si USE_TZ=True)")
    fin = models.DateTimeField(help_text="Fecha y hora de fin (debe ser posterior a inicio)")
    habilitada = models.BooleanField(
        default=True,
        help_text="Permite desactivar la ventana temporal sin borrar fechas",
    )

    banner = models.ImageField(
        upload_to="banners/",
        blank=True,
        null=True,
        help_text="Imagen para mostrar cuando la aplicación no esté disponible",
    )

    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de campaña"
        verbose_name_plural = "Configuración de campaña"

    def __str__(self):
        return f"Campaña del {self.inicio} al {self.fin} (habilitada={self.habilitada})"

    def esta_activa(self, ahora=None):
        if not self.habilitada:
            return False
        ahora = ahora or timezone.now()
        return self.inicio <= ahora <= self.fin

    def no_ha_iniciado(self, ahora=None):
        ahora = ahora or timezone.now()
        return self.habilitada and ahora < self.inicio

    def ya_finalizo(self, ahora=None):
        ahora = ahora or timezone.now()
        return self.habilitada and ahora > self.fin


def politica_upload_to(instance, filename):
    # Guarda el PDF en media/politicas/<id>/<filename>
    return f"politicas/{instance.id or 'tmp'}/{filename}"


class PoliticaCompra(models.Model):
    """
    Configuración de la política de compra a mostrar en el modal.
    Provee un PDF opcional y/o un enlace externo.
    """

    titulo = models.CharField(max_length=150, default="Política de compra de herramientas")
    pdf = models.FileField(upload_to=politica_upload_to, blank=True, null=True)
    enlace = models.URLField(blank=True, null=True, help_text="Enlace externo (Drive, SharePoint, etc.)")
    activo = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Política de compra"
        verbose_name_plural = "Política de compra"

    def __str__(self):
        return f"{self.titulo} (activo={self.activo})"

    def tiene_contenido(self) -> bool:
        return bool(self.pdf or self.enlace)


def masinfo_upload_to(instance, filename):
    return f"masinfo/{instance.id or 'tmp'}/{filename}"


class MasInfo(models.Model):
    titulo = models.CharField(max_length=150, default="Más información")
    imagen = models.ImageField(upload_to=masinfo_upload_to, blank=True, null=True)
    activo = models.BooleanField(default=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Más info"
        verbose_name_plural = "Más info"

    def __str__(self) -> str:
        return f"{self.titulo} (activo={self.activo})"

    def tiene_imagen(self) -> bool:
        return bool(self.imagen)

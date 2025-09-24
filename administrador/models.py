from django.db import models
from django.utils import timezone


class CampaniaConfig(models.Model):
    """
    Configuración de la campaña. Normalmente habrá SOLO un registro (pk=1).
    """

    inicio = models.DateTimeField(help_text="Fecha y hora de inicio (UTC por defecto si USE_TZ=True)")
    fin = models.DateTimeField(help_text="Fecha y hora de fin (debe ser posterior a inicio)")
    habilitada = models.BooleanField(default=True, help_text="Permite desactivar la ventana temporal sin borrar fechas")

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

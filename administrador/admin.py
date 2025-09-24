from django.contrib import admin

from .models import CampaniaConfig


@admin.register(CampaniaConfig)
class CampaniaConfigAdmin(admin.ModelAdmin):
    list_display = ("inicio", "fin", "habilitada", "actualizado")

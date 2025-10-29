from __future__ import annotations

from datetime import datetime, time

from django import forms
from django.utils import timezone

from .models import CampaniaConfig, MasInfo, PoliticaCompra


class CampaniaForm(forms.Form):
    fecha_inicio = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hora_inicio = forms.TimeField(
        label="Hora de inicio (24h)",
        widget=forms.TimeInput(attrs={"type": "time"}),
        initial=time(8, 0),
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hora_fin = forms.TimeField(
        label="Hora de fin (24h)",
        widget=forms.TimeInput(attrs={"type": "time"}),
        initial=time(20, 30),
    )
    banner = forms.ImageField(label="Banner (opcional)", required=False)

    def __init__(self, *args, instance: CampaniaConfig | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

        for name in ["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin", "banner"]:
            if name in self.fields:
                self.fields[name].widget.attrs.update({"class": "input-sm"})

        if instance and not self.is_bound:
            tz = timezone.get_current_timezone()
            ini = timezone.localtime(instance.inicio, tz)
            fin = timezone.localtime(instance.fin, tz)
            self.fields["fecha_inicio"].initial = ini.date()
            self.fields["hora_inicio"].initial = ini.time().replace(microsecond=0)
            self.fields["fecha_fin"].initial = fin.date()
            self.fields["hora_fin"].initial = fin.time().replace(microsecond=0)

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get("fecha_inicio")
        hi = cleaned.get("hora_inicio")
        ff = cleaned.get("fecha_fin")
        hf = cleaned.get("hora_fin")
        if not all([fi, hi, ff, hf]):
            return cleaned

        ini = datetime.combine(fi, hi)
        fin = datetime.combine(ff, hf)
        if fin <= ini:
            raise forms.ValidationError("La fecha/hora de fin debe ser posterior a la de inicio.")

        delta = fin - ini
        if delta.days > 999:
            raise forms.ValidationError("La campaña no puede exceder 999 días.")

        for t, nombre in [(hi, "inicio"), (hf, "fin")]:
            if not (0 <= t.hour <= 23):
                raise forms.ValidationError(f"La hora de {nombre} debe estar entre 0 y 23.")
            if not (0 <= t.minute <= 59):
                raise forms.ValidationError(f"Los minutos de {nombre} deben estar entre 0 y 59.")
            if not (0 <= t.second <= 59):
                raise forms.ValidationError(f"Los segundos de {nombre} deben estar entre 0 y 59.")

        tz = timezone.get_current_timezone()
        cleaned["inicio_dt"] = timezone.make_aware(ini, tz)
        cleaned["fin_dt"] = timezone.make_aware(fin, tz)
        return cleaned

    def save(self, commit: bool = True) -> CampaniaConfig:
        if not self.instance:
            self.instance = CampaniaConfig()
        self.instance.inicio = self.cleaned_data["inicio_dt"]
        self.instance.fin = self.cleaned_data["fin_dt"]
        self.instance.habilitada = True

        banner = self.cleaned_data.get("banner")
        if banner is not None:
            self.instance.banner = banner

        if commit:
            self.instance.save()
        return self.instance


class PoliticaCompraForm(forms.ModelForm):
    class Meta:
        model = PoliticaCompra
        fields = ["titulo", "pdf", "enlace", "activo"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "input-sm"}),
            "enlace": forms.URLInput(attrs={"class": "input-sm"}),
        }

    def clean_pdf(self):
        pdf = self.cleaned_data.get("pdf")
        if pdf and pdf.content_type not in ("application/pdf",):
            raise forms.ValidationError("Solo se permite subir archivos PDF.")
        return pdf

    def clean(self):
        cleaned = super().clean()
        pdf = cleaned.get("pdf")
        enlace = cleaned.get("enlace")
        activo = cleaned.get("activo")

        if activo and not (pdf or enlace):
            raise forms.ValidationError("Si la política está activa, debes subir un PDF y/o proporcionar un enlace.")
        return cleaned


class MasInfoForm(forms.ModelForm):
    class Meta:
        model = MasInfo
        fields = ["titulo", "imagen", "activo"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "input-sm"}),
        }

    def clean_imagen(self):
        img = self.cleaned_data.get("imagen")
        if img and img.content_type not in ("image/png", "image/jpeg", "image/webp"):
            raise forms.ValidationError("Formatos permitidos: PNG, JPG/JPEG o WEBP.")
        return img

# forms.py
from django import forms

from .models import Producto, ProductoImagen


class ActualizarStockMinimoForm(forms.Form):
    sku = forms.CharField(label="SKU", max_length=100)
    stock = forms.IntegerField(label="Stock", min_value=0)
    minimo_pedido = forms.IntegerField(label="Mínimo para pedido", min_value=1)


class ExcelUploadForm(forms.Form):
    archivo1 = forms.FileField(
        label="Archivo Excel 1 (Productos)",
        help_text="Debe contener: SKU, DESCRICIÓN, SBU, CATEGORÍA, PRECIO ANTES DE IVA",
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls"}),
    )
    archivo2 = forms.FileField(
        label="Archivo Excel 2 (Empaque)",
        help_text="Debe contener: SKU, UND EMPAQUE",
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls"}),
    )


class ImagenUploadForm(forms.ModelForm):
    sku = forms.CharField(max_length=100, required=True)  # cambiar referencia por sku

    class Meta:
        model = ProductoImagen
        fields = ["imagen"]  # imagen sigue igual

    def clean_sku(self):
        sku = self.cleaned_data.get("sku")
        if not Producto.objects.filter(sku=sku).exists():
            raise forms.ValidationError("El SKU no existe en la base de datos")
        return sku

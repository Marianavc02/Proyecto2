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


class FiltroProductosForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={"placeholder": "Buscar productos...", "class": "search-input"}),
    )

    categoria = forms.ChoiceField(
        required=False, label="Categoría", widget=forms.Select(attrs={"class": "filter-select"})
    )
    min_precio = forms.DecimalField(
        required=False,
        min_value=0,
        label="Precio mínimo",
        widget=forms.NumberInput(attrs={"placeholder": "Mínimo", "class": "price-input"}),
    )

    max_precio = forms.DecimalField(
        required=False,
        min_value=0,
        label="Precio máximo",
        widget=forms.NumberInput(attrs={"placeholder": "Máximo", "class": "price-input"}),
    )

    def __init__(self, *args, **kwargs):
        categorias = kwargs.pop("categorias", [])
        super().__init__(*args, **kwargs)
        # Opciones para el campo categoría
        opciones_categorias = [("", "Todas las categorías")]
        for cat in categorias:
            if cat:  # Solo agregar categorías no vacías
                opciones_categorias.append((cat, cat))
        self.fields["categoria"].choices = opciones_categorias

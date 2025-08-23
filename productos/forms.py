# forms.py
from django import forms
from .models import Producto, ProductoImagen

class ExcelUploadForm(forms.Form):
    archivo = forms.FileField(
        label='Seleccione archivo Excel',
        help_text='Formatos soportados: XLSX',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

class ImagenUploadForm(forms.ModelForm):
    sku = forms.CharField(max_length=100, required=True)  # cambiar referencia por sku

    class Meta:
        model = ProductoImagen
        fields = ['imagen']  # imagen sigue igual

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if not Producto.objects.filter(sku=sku).exists():
            raise forms.ValidationError("El SKU no existe en la base de datos")
        return sku

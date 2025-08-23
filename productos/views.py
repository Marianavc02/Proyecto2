# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Producto, ProductoImagen
from .forms import ExcelUploadForm, ImagenUploadForm

# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Producto, ProductoImagen
from .forms import ExcelUploadForm, ImagenUploadForm

def cargar_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                archivo = request.FILES['archivo']
                df = pd.read_excel(archivo, decimal=",")

                # Normalizar nombres de columnas
                df.columns = [col.strip().upper() for col in df.columns]

                # Columnas requeridas en el Excel
                columnas_requeridas = ['SKU', 'DESCRICIÓN', 'SBU', 'CATEGORÍA', 'PRECIO ANTES DE IVA']

                if not all(col in df.columns for col in columnas_requeridas):
                    messages.error(request, f'El archivo no tiene las columnas requeridas. Columnas encontradas: {df.columns.tolist()}')
                    return redirect('cargar_excel')

                # Procesar cada fila
                for _, row in df.iterrows():
                    Producto.objects.update_or_create(
                        sku=row['SKU'],  # <-- aquí usamos sku
                        defaults={
                            'descripcion': row['DESCRICIÓN'],
                            'sbu': row['SBU'],
                            'categoria': row['CATEGORÍA'],
                            'precio_sin_iva': row['PRECIO ANTES DE IVA'],
                        }
                    )

                messages.success(request, 'Productos cargados exitosamente')
                return redirect('lista_productos')

            except Exception as e:
                messages.error(request, f'Error al procesar el archivo: {str(e)}')
                return redirect('cargar_excel')
    else:
        form = ExcelUploadForm()

    return render(request, 'productos/cargar_excel.html', {'form': form})


def lista_productos(request):
    productos = Producto.objects.all().prefetch_related('imagenes')
    return render(request, 'productos/lista_productos.html', {'productos': productos})

def cargar_imagen(request):
    if request.method == 'POST':
        form = ImagenUploadForm(request.POST, request.FILES)
        if form.is_valid():
            sku = form.cleaned_data['sku']  # ahora usamos SKU
            imagen = form.cleaned_data['imagen']
            
            try:
                producto = Producto.objects.get(sku=sku)  # buscar por SKU
                ProductoImagen.objects.create(producto=producto, imagen=imagen)
                messages.success(request, 'Imagen cargada exitosamente')
                return redirect('lista_productos')
            except Producto.DoesNotExist:
                messages.error(request, 'Producto no encontrado')
    else:
        form = ImagenUploadForm()
    
    return render(request, 'productos/cargar_imagen.html', {'form': form})

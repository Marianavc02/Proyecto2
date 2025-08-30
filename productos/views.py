# views.py
import pandas as pd
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse

from .models import Producto, ProductoImagen
from .forms import ExcelUploadForm, ImagenUploadForm
from .utils import clasificar_empresa



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

#View para mostrar productos según empresa

def productos_por_empresa(request, empresa):
    productos = Producto.objects.filter(empresa=empresa)  
    return render(request, 'productos/productos_por_empresa.html', {
        'empresa': empresa,
        'productos': productos
    })

#View para mostrar detalle producto
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'productos/detalle_producto.html', {'producto': producto})

#<--!"{% url 'producto_detalle' producto.pk %}"-->


# CARRITO (sesión)  RF_12-RF_14

MAX_ITEMS = 5
SESSION_KEY = "carrito"

def _get_cart(request):
    return request.session.get(SESSION_KEY, {})

def _save_cart(request, cart):
    request.session[SESSION_KEY] = cart
    request.session.modified = True

def carrito_agregar(request, sku):
    """
    RF_12: Agregar producto al carrito (máx. 5, sin repetidos).
    """
    if request.method != "POST":
        return redirect("carrito_ver")

    cart = _get_cart(request)

    # Límite de 5 productos distintos
    if sku not in cart and len(cart.keys()) >= MAX_ITEMS:
        messages.warning(request, "No puedes agregar más de 5 productos al carrito.")
        return redirect("carrito_ver")

    # No permitir repetidos
    if sku in cart:
        messages.warning(request, "Este producto ya está en tu carrito.")
        return redirect("carrito_ver")

    # Buscar el producto por SKU
    try:
        producto = Producto.objects.get(sku=sku)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect("carrito_ver")

    # Tomar la primera imagen si existe
    first_img = producto.imagenes.first()
    img_url = first_img.imagen.url if first_img else ""

    # Guardamos solo 1 unidad por requisito (una referencia por producto)
    cart[sku] = {
        "sku": producto.sku,
        "descripcion": producto.descripcion,
        "precio": str(producto.precio_sin_iva or Decimal("0")),
        "categoria": producto.categoria or "",
        "imagen_url": img_url,
    }
    _save_cart(request, cart)
    messages.success(request, "Producto agregado al carrito.")
    return redirect("carrito_ver")

def carrito_eliminar(request, sku):
    """
    RF_13: Eliminar producto del carrito.
    """
    cart = _get_cart(request)
    if sku in cart:
        cart.pop(sku)
        _save_cart(request, cart)
        if not cart:
            messages.info(request, "Carrito vacío.")
        else:
            messages.success(request, "Producto eliminado del carrito.")
    else:
        messages.warning(request, "Ese producto no estaba en tu carrito.")
    return redirect("carrito_ver")

def carrito_ver(request):
    """
    RF_14: Ver carrito + resumen (subtotal/total).
    """
    cart = _get_cart(request)
    items = []
    total = Decimal("0")

    for sku, data in cart.items():
        precio = Decimal(data.get("precio", "0"))
        subtotal = precio  # cantidad fija = 1 (no repetidos)
        total += subtotal
        items.append({
            "sku": sku,
            "descripcion": data.get("descripcion", ""),
            "precio": precio,
            "subtotal": subtotal,
            "categoria": data.get("categoria", ""),
            "imagen_url": data.get("imagen_url", ""),
        })

    contexto = {
        "items": items,
        "total": total,
        "max_items": MAX_ITEMS,
        "count": len(items),
    }
    return render(request, "productos/carrito.html", contexto)
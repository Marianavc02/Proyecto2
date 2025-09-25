# views.py
from decimal import Decimal

import pandas as pd
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExcelUploadForm, ImagenUploadForm

# from django.urls import reverse
from .models import Pedido, PedidoItem, Producto, ProductoImagen


def cargar_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                archivo1 = request.FILES["archivo1"]
                archivo2 = request.FILES["archivo2"]

                df1 = pd.read_excel(archivo1, decimal=",")
                df2 = pd.read_excel(archivo2, decimal=",")

                # Normalizar columnas
                df1.columns = [col.strip().upper() for col in df1.columns]
                df2.columns = [col.strip().upper() for col in df2.columns]

                # Columnas requeridas
                cols_excel1 = ["SKU", "DESCRICIÓN", "SBU", "CATEGORÍA", "PRECIO ANTES DE IVA"]
                cols_excel2 = ["SKU", "UND EMPAQUE"]

                # Validaciones
                if not all(c in df1.columns for c in cols_excel1):
                    messages.error(
                        request,
                        f"Archivo 1 inválido. Columnas encontradas: {df1.columns.tolist()}",
                    )
                    return redirect("cargar_excel")

                if not all(c in df2.columns for c in cols_excel2):
                    messages.error(
                        request,
                        f"Archivo 2 inválido. Columnas encontradas: {df2.columns.tolist()}",
                    )
                    return redirect("cargar_excel")

                # Quedarse con lo necesario
                df1 = df1[cols_excel1]
                df2 = df2[cols_excel2]

                # Unir por SKU
                df_final = pd.merge(df1, df2, on="SKU", how="left")

                # Guardar en la BD
                for _, row in df_final.iterrows():
                    # Tomamos el valor de UND EMPAQUE y si está vacío lo dejamos en 0
                    minimo_pedido = row.get("UND EMPAQUE", 0)
                    if pd.isna(minimo_pedido):
                        minimo_pedido = 0

                    Producto.objects.update_or_create(
                        sku=row["SKU"],
                        defaults={
                            "descripcion": row["DESCRICIÓN"],
                            "sbu": row["SBU"],
                            "categoria": row["CATEGORÍA"],
                            "precio_sin_iva": row["PRECIO ANTES DE IVA"],
                            "minimo_pedido": minimo_pedido,  # 👈 ya controlado
                        },
                    )
                messages.success(request, "Productos cargados exitosamente")
                return redirect("lista_productos")

            except Exception as e:
                messages.error(request, f"Error al procesar los archivos: {str(e)}")
                return redirect("cargar_excel")
    else:
        form = ExcelUploadForm()

    return render(request, "productos/cargar_excel.html", {"form": form})


def lista_productos(request):
    productos = Producto.objects.all().prefetch_related("imagenes")
    return render(request, "productos/lista_productos.html", {"productos": productos})


def cargar_imagen(request):
    if request.method == "POST":
        form = ImagenUploadForm(request.POST, request.FILES)
        if form.is_valid():
            sku = form.cleaned_data["sku"]  # ahora usamos SKU
            imagen = form.cleaned_data["imagen"]

            try:
                producto = Producto.objects.get(sku=sku)  # buscar por SKU
                ProductoImagen.objects.create(producto=producto, imagen=imagen)
                messages.success(request, "Imagen cargada exitosamente")
                return redirect("lista_productos")
            except Producto.DoesNotExist:
                messages.error(request, "Producto no encontrado")
    else:
        form = ImagenUploadForm()

    return render(request, "productos/cargar_imagen.html", {"form": form})


# View para mostrar productos según empresa
def productos_por_empresa(request, empresa):
    productos = Producto.objects.filter(empresa__iexact=empresa)

    # Obtener filtros de GET
    marca = request.GET.get("marca")
    categoria = request.GET.get("categoria")
    min_precio = request.GET.get("min_precio")
    max_precio = request.GET.get("max_precio")

    # Filtros dinámicos
    if marca and marca.strip():
        productos = productos.filter(empresa__icontains=marca.strip())
    if categoria and categoria.strip():
        productos = productos.filter(categoria__icontains=categoria.strip())
    if min_precio:
        try:
            productos = productos.filter(precio_sin_iva__gte=float(min_precio))
        except ValueError:
            pass
    if max_precio:
        try:
            productos = productos.filter(precio_sin_iva__lte=float(max_precio))
        except ValueError:
            pass

    return render(
        request,
        "productos/productos_por_empresa.html",
        {"productos": productos, "empresa": empresa},
    )


# View para mostrar detalle producto
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    # Contar cuántos hay en el carrito de este usuario (por sesión)
    pedidos = 0
    cart = request.session.get("carrito", {})
    if producto.sku in cart:
        pedidos = 1  # solo 1 por usuario según lógica actual
    # Para AJAX: si es petición JS, devolver solo el estado
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        faltan = max(0, producto.minimo_pedido - pedidos)
        return JsonResponse(
            {
                "pedidos": pedidos,
                "minimo_pedido": producto.minimo_pedido,
                "cumplido": pedidos >= producto.minimo_pedido,
                "faltan": faltan,
            }
        )
    faltan = max(0, producto.minimo_pedido - pedidos)
    return render(
        request,
        "productos/detalle_producto.html",
        {"producto": producto, "pedidos": pedidos, "faltan": faltan, "cumplido": pedidos >= producto.minimo_pedido},
    )


# <--!"{% url 'producto_detalle' producto.pk %}"-->


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
        "empresa": producto.empresa or "",
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

    productos_no_cumplen = []
    for sku, data in cart.items():
        precio = Decimal(data.get("precio", "0"))
        subtotal = precio  # cantidad fija = 1 (no repetidos)
        total += subtotal

        # Buscar el producto real para validar el mínimo
        try:
            producto = Producto.objects.get(sku=sku)
            cantidad_en_carrito = 1  # si implementas cantidades, cámbialo aquí
            cumple_minimo = cantidad_en_carrito >= producto.minimo_pedido
            if not cumple_minimo:
                faltan = producto.minimo_pedido - cantidad_en_carrito
                productos_no_cumplen.append(
                    {
                        "sku": sku,
                        "descripcion": producto.descripcion,
                        "minimo_pedido": producto.minimo_pedido,
                        "faltan": faltan,
                    }
                )
        except Producto.DoesNotExist:
            pass

        items.append(
            {
                "sku": sku,
                "descripcion": data.get("descripcion", ""),
                "precio": precio,
                "subtotal": subtotal,
                "categoria": data.get("categoria", ""),
                "imagen_url": data.get("imagen_url", ""),
            }
        )

    contexto = {
        "items": items,
        "total": total,
        "max_items": MAX_ITEMS,
        "count": len(items),
        "productos_no_cumplen": productos_no_cumplen,
    }
    return render(request, "productos/carrito.html", contexto)


def actualizar_stock_minimo(request):
    from .forms import ActualizarStockMinimoForm

    producto = None
    form = None
    sku = None
    if request.method == "POST":
        # En buscar usamos el campo 'sku' del input; en actualizar usamos 'sku_confirmado'
        if "buscar" in request.POST:
            sku = request.POST.get("sku")
            try:
                producto = Producto.objects.get(sku=sku)
                form = ActualizarStockMinimoForm(
                    initial={"sku": producto.sku, "stock": producto.stock, "minimo_pedido": producto.minimo_pedido}
                )
            except Producto.DoesNotExist:
                producto = None
                form = ActualizarStockMinimoForm(initial={"sku": sku})
                messages.error(request, f"No se encontró el producto con SKU {sku}")
        elif "actualizar" in request.POST:
            sku = request.POST.get("sku_confirmado") or request.POST.get("sku")
            form = ActualizarStockMinimoForm(request.POST)
            if form.is_valid():
                stock = form.cleaned_data["stock"]
                minimo_pedido = form.cleaned_data["minimo_pedido"]
                try:
                    producto = Producto.objects.get(sku=sku)
                    producto.stock = stock
                    producto.minimo_pedido = minimo_pedido
                    producto.save()
                    messages.success(request, f"Stock y mínimo de pedido actualizados para {sku}")
                except Producto.DoesNotExist:
                    producto = None
                    messages.error(request, f"No se encontró el producto con SKU {sku}")
            else:
                producto = None
                messages.error(request, "Formulario inválido")
    else:
        form = ActualizarStockMinimoForm()
    return render(request, "productos/actualizar_stock_minimo.html", {"form": form, "producto": producto, "sku": sku})


def buscar_productos(request):
    query = request.GET.get("q", "")
    categoria = request.GET.get("categoria", "")
    min_precio = request.GET.get("min_precio", "")
    max_precio = request.GET.get("max_precio", "")
    productos = Producto.objects.all()
    if query:
        productos = productos.filter(
            models.Q(descripcion__icontains=query)
            | models.Q(sku__icontains=query)
            | models.Q(categoria__icontains=query)
        )
    if categoria:
        productos = productos.filter(categoria__icontains=categoria)
    if min_precio:
        try:
            productos = productos.filter(precio_sin_iva__gte=float(min_precio))
        except ValueError:
            pass
    if max_precio:
        try:
            productos = productos.filter(precio_sin_iva__lte=float(max_precio))
        except ValueError:
            pass
    return render(request, "productos/buscar_productos.html", {"productos": productos, "query": query})


def enviar_pedido(request):
    cart = _get_cart(request)
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("carrito_ver")

    # Crear el pedido
    if request.user.is_authenticated:
        pedido = Pedido.objects.create(usuario=request.user)
    else:
        pedido = Pedido.objects.create()

    # Crear los items
    for sku, data in cart.items():
        try:
            producto = Producto.objects.get(sku=sku)
            PedidoItem.objects.create(pedido=pedido, producto=producto, cantidad=1)
        except Producto.DoesNotExist:
            continue

    # Vaciar carrito
    request.session[SESSION_KEY] = {}
    request.session.modified = True

    messages.success(request, f"Tu pedido #{pedido.id} ha sido enviado correctamente.")
    return redirect("administrador:reporte_pedidos")

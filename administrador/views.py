import openpyxl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem

from .forms import CampaniaForm
from .utils import obtener_config


@login_required
def base_admin(request):
    """Renderiza la plantilla base del panel de administrador.

    Protegido para usuarios autenticados; si no es staff, redirige al inicio.
    """
    if not request.user.is_staff:
        return redirect("/")
    return render(request, "administrador/base_admin.html")


def programar_fechas(request):
    cfg = obtener_config()

    if request.method == "POST":
        # Acción: eliminar (deja todo en “no programado” y contador en 0)
        if "eliminar" in request.POST:
            ahora = timezone.now()
            cfg.inicio = ahora
            cfg.fin = ahora
            cfg.habilitada = False
            cfg.save()
            messages.success(request, "Campaña eliminada. No hay campaña programada.")
            return redirect("administrador:programar_fechas")
        # Acción: confirmar (guardar fechas)
        form = CampaniaForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Fechas de campaña guardadas!")
            return redirect("administrador:programar_fechas")
    else:
        form = CampaniaForm(instance=cfg)

    return render(request, "administrador/programar_fechas.html", {"form": form, "cfg": cfg})


def estado_campania(request):
    cfg = obtener_config()
    ahora = timezone.now()
    contexto = {
        "cfg": cfg,
        "ahora_iso": ahora.isoformat(),
        "inicio_iso": cfg.inicio.isoformat(),
        "fin_iso": cfg.fin.isoformat(),
        "activa": cfg.esta_activa(ahora),
        "no_ha_iniciado": cfg.no_ha_iniciado(ahora),
        "ya_finalizo": cfg.ya_finalizo(ahora),
    }
    return render(request, "administrador/estado_campania.html", contexto)


def reporte_pedidos(request):
    query = request.GET.get("q", "")  # texto buscado
    reporte = PedidoItem.objects.values("producto__sku", "producto__descripcion").annotate(
        num_pedidos=Count("pedido", distinct=True)
    )

    # si hay búsqueda, filtramos
    if query:
        reporte = reporte.filter(Q(producto__sku__icontains=query) | Q(producto__descripcion__icontains=query))

    reporte = reporte.order_by("-num_pedidos")

    return render(
        request,
        "administrador/reporte_pedidos.html",
        {"reporte": reporte, "query": query},  # pasamos el query al template
    )


def exportar_reporte_excel(request):
    # Obtener los productos con su conteo de pedidos
    query = request.GET.get("q", "")
    reporte = PedidoItem.objects.values("producto__sku", "producto__descripcion").annotate(
        num_pedidos=Count("pedido", distinct=True)
    )

    # Filtrar si hay búsqueda
    if query:
        reporte = reporte.filter(Q(producto__sku__icontains=query) | Q(producto__descripcion__icontains=query))

    reporte = reporte.order_by("-num_pedidos")

    # Crear archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Productos"

    # Encabezados
    ws.append(["SKU", "Nombre del Producto", "Veces Pedido"])

    # Agregar datos
    for item in reporte:
        ws.append(
            [
                item["producto__sku"],
                item["producto__descripcion"],
                item["num_pedidos"],
            ]
        )

    # Respuesta HTTP con el Excel
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="reporte_productos.xlsx"'
    wb.save(response)
    return response


def reporte_pedidos_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    pedidos = Pedido.objects.filter(empleado=empleado).prefetch_related("items__producto")
    pedidos_data = []
    total_general = 0

    for pedido in pedidos:
        subtotal = sum(item.cantidad * item.producto.precio_sin_iva for item in pedido.items.all())
        pedidos_data.append(
            {
                "pedido": pedido,
                "items": pedido.items.all(),
                "subtotal": subtotal,
            }
        )
        total_general += subtotal

    return render(
        request,
        "administrador/reporte_pedidos_empleado.html",
        {
            "empleado": empleado,
            "pedidos_data": pedidos_data,
            "total_general": total_general,
        },
    )


def lista_empleados_reporte(request):
    query = request.GET.get("q", "")  # Capturamos el texto de búsqueda

    # Filtramos por nombre o correo si hay búsqueda
    empleados = Empleado.objects.all()
    if query:
        empleados = empleados.filter(Q(preferred_name__icontains=query) | Q(sbd_email__icontains=query))

    return render(
        request,
        "administrador/lista_empleados_reporte.html",
        {"empleados": empleados, "query": query},
    )


def exportar_reporte_empleado_excel(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)

    # Obtener los pedidos del empleado y sus productos
    pedidos = Pedido.objects.filter(empleado=empleado).prefetch_related("items__producto")

    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Pedidos de {empleado.preferred_name}"

    # Encabezados
    ws.append(["ID Pedido", "Fecha", "SKU Producto", "Descripción", "Cantidad", "Precio Unitario", "Subtotal"])

    # Agregar filas
    for pedido in pedidos:
        for item in pedido.items.all():
            subtotal = item.cantidad * item.producto.precio
            ws.append(
                [
                    pedido.id,
                    pedido.fecha.strftime("%Y-%m-%d %H:%M"),
                    item.producto.sku,
                    item.producto.descripcion,
                    item.cantidad,
                    item.producto.precio,
                    subtotal,
                ]
            )

    # Configurar la respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"reporte_empleado_{empleado.preferred_name}.xlsx".replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

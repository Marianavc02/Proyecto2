import openpyxl
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from productos.models import PedidoItem

from .forms import CampaniaForm
from .utils import obtener_config


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
    # Creamos un nuevo libro Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pedidos"

    # Encabezados
    ws.append(["ID Pedido", "Usuario", "Fecha", "Producto SKU", "Producto Descripción", "Cantidad"])

    # Traemos los datos de PedidoItem (con joins)
    items = PedidoItem.objects.select_related("pedido", "producto").all()

    for item in items:
        ws.append(
            [
                item.pedido.id,
                item.pedido.usuario.username if item.pedido.usuario else "Anónimo",
                item.pedido.fecha.strftime("%Y-%m-%d %H:%M"),
                item.producto.sku,
                item.producto.descripcion,
                item.cantidad,
            ]
        )

    # Respuesta HTTP con Excel
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="reporte_pedidos.xlsx"'
    wb.save(response)

    return response

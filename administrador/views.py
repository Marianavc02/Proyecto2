from datetime import datetime

import openpyxl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem

from .decorators import staff_required
from .forms import CampaniaForm
from .utils import obtener_config


@login_required
@staff_required()
def base_admin(request):
    """Renderiza la plantilla base del panel de administrador.

    Protegido para usuarios autenticados; si no es staff, redirige al inicio.
    """
    if not request.user.is_staff:
        return redirect("/")
    return render(request, "administrador/base_admin.html")


@login_required
@staff_required()
def programar_fechas(request):
    cfg = obtener_config()

    if request.method == "POST":

        # Acción: eliminar campaña completa
        if "eliminar" in request.POST:
            ahora = timezone.now()
            cfg.inicio = ahora
            cfg.fin = ahora
            cfg.habilitada = False
            cfg.banner = None
            cfg.save()
            messages.success(request, "Campaña eliminada. No hay campaña programada.")
            return redirect("administrador:programar_fechas")

        # Acción: guardar banner
        if "guardar_banner" in request.POST:
            banner = request.FILES.get("banner")
            if banner:
                cfg.banner = banner
                cfg.save()
                messages.success(request, "Banner actualizado correctamente.")
            else:
                messages.warning(request, "No seleccionaste ninguna imagen.")
            return redirect("administrador:programar_fechas")

        # Acción: eliminar solo el banner
        if "eliminar_banner" in request.POST:
            if cfg.banner:
                cfg.banner.delete(save=False)
                cfg.banner = None
                cfg.save()
                messages.success(request, "Banner eliminado. Se mostrará el logo por defecto.")
            else:
                messages.warning(request, "No hay ningún banner para eliminar.")
            return redirect("administrador:programar_fechas")

        # Acción: guardar fechas de campaña
        form = CampaniaForm(request.POST, request.FILES, instance=cfg)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Fechas de campaña guardadas correctamente!")
            return redirect("administrador:programar_fechas")

    else:
        form = CampaniaForm(instance=cfg)

    return render(request, "administrador/programar_fechas.html", {"form": form, "cfg": cfg})


@login_required
@staff_required()
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


@login_required
@staff_required()
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


@login_required
@staff_required()
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


@login_required
@staff_required()
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


@login_required
@staff_required()
def lista_empleados_reporte(request):
    query = request.GET.get("q", "").strip()

    empleados = Empleado.objects.all()

    if query:
        # 🔹 Filtrar empleados por nombre o correo
        empleados_por_nombre = Empleado.objects.filter(
            Q(preferred_name__icontains=query) | Q(sbd_email__icontains=query)
        )

        # 🔹 Filtrar empleados que tengan pedidos con productos que coincidan por nombre o SKU
        empleados_por_producto = Empleado.objects.filter(
            Q(pedidos__items__producto__descripcion__icontains=query)
            | Q(pedidos__items__producto__sku__icontains=query)
        )

        # 🔹 Unir ambos resultados y eliminar duplicados
        empleados = (empleados_por_nombre | empleados_por_producto).distinct()

    return render(
        request,
        "administrador/lista_empleados_reporte.html",
        {"empleados": empleados, "query": query},
    )


@login_required
@staff_required()
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
            subtotal = item.cantidad * item.producto.precio_sin_iva
            ws.append(
                [
                    pedido.id,
                    pedido.fecha.strftime("%Y-%m-%d %H:%M"),
                    item.producto.sku,
                    item.producto.descripcion,
                    item.cantidad,
                    item.producto.precio_sin_iva,
                    subtotal,
                ]
            )

    # Configurar la respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    filename = f"reporte_empleado_{empleado.preferred_name}.xlsx".replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
@staff_required()
def modificar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    items = pedido.items.all()  # Ajusta si el nombre del related_name es distinto

    if request.method == "POST":
        item_id = request.POST.get("item_id")
        item = get_object_or_404(PedidoItem, id=item_id, pedido=pedido)
        item.delete()
        return redirect("administrador:modificar_pedido", pedido_id=pedido.id)

    context = {
        "pedido": pedido,
        "items": items,
    }
    return render(request, "administrador/modificar_pedido.html", context)


def generar_acta_entrega(request, pedido_id):
    """
    Genera un acta de constancia de entrega en formato PDF
    para un pedido específico realizado por un empleado.
    """

    # Buscar el pedido o mostrar error si no existe
    pedido = get_object_or_404(Pedido, id=pedido_id)
    empleado = pedido.empleado
    items = pedido.items.all()

    # Crear la respuesta HTTP con tipo de contenido PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="acta_entrega_pedido_{pedido.id}.pdf"'

    # Crear el documento PDF
    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # === ENCABEZADO ===
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 50, "ACTA DE CONSTANCIA DE ENTREGA DE HERRAMIENTAS")
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, height - 70, "Ciudad de Medellín — Empresa Stanley Black & Decker Colombia S.A.S")

    # === DATOS DEL EMPLEADO ===
    y = height - 120
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Datos del empleado:")
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(70, y, f"Nombre: {empleado.preferred_name}")
    y -= 15
    pdf.drawString(70, y, f"Correo: {empleado.sbd_email}")
    y -= 15
    pdf.drawString(70, y, f"ID interno: {empleado.id}")
    y -= 30

    # === TEXTO DE CONSTANCIA ===
    pdf.setFont("Helvetica", 10)
    texto = (
        f"Se hace constancia de la entrega del pedido al empleado {empleado.preferred_name}, "
        f"identificado con cédula de ciudadanía __________________, con ID {empleado.id}, "
        f"de los siguientes ítems por el valor correspondiente, el día {pedido.fecha.strftime('%d/%m/%Y')}."
    )
    pdf.drawString(50, y, texto)
    y -= 40

    # === TABLA DE PRODUCTOS ENTREGADOS ===
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, y, "Ítems entregados:")
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(60, y, "Descripción")
    pdf.drawString(300, y, "Referencia (SKU)")
    pdf.drawString(450, y, "Cantidad")
    y -= 15
    pdf.line(50, y, 550, y)
    y -= 10

    total = 0
    for item in items:
        if y < 100:  # salto de página si no cabe
            pdf.showPage()
            y = height - 100
        pdf.drawString(60, y, item.producto.descripcion[:40])  # corta descripción larga
        pdf.drawString(300, y, item.producto.sku)
        pdf.drawString(470, y, str(item.cantidad))
        if item.producto.precio_sin_iva:
            total += float(item.producto.precio_sin_iva) * item.cantidad
        y -= 15

    # === TOTAL ===
    y -= 10
    pdf.line(50, y, 550, y)
    y -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(400, y, f"Valor total: ${total:,.2f}")
    y -= 40

    # === FIRMAS ===
    pdf.setFont("Helvetica", 10)
    pdf.drawString(100, y, "_________________________")
    pdf.drawString(370, y, "_________________________")
    y -= 15
    pdf.drawString(120, y, "Firma del Empleado")
    pdf.drawString(390, y, "Firma de quien entrega")

    # === FECHA Y CIERRE ===
    y -= 40
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(50, y, f"Generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    pdf.showPage()
    pdf.save()

    return response

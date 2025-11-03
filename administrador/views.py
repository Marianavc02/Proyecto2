from __future__ import annotations

from datetime import datetime
import textwrap

import openpyxl
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas

from empleados.models import Empleado
from productos.models import Pedido, PedidoItem

from .decorators import staff_required
from .forms import CampaniaForm, MasInfoForm, PoliticaCompraForm
from .models import MasInfo, PoliticaCompra, CampaniaConfig
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

    # Historial de campañas para mostrar bajo el banner
    from administrador.models import CampaniaHistorial
    historial = CampaniaHistorial.objects.all()[:20]

    return render(
        request,
        "administrador/programar_fechas.html",
        {"form": form, "cfg": cfg, "historial": historial},
    )


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
    from administrador.models import CampaniaHistorial
    query = request.GET.get("q", "")  # texto buscado
    campania_id = request.GET.get("campania", "")
    campañas = CampaniaHistorial.objects.all().order_by("-inicio")

    reporte = PedidoItem.objects.values("producto__sku", "producto__descripcion").annotate(
        num_pedidos=Count("pedido", distinct=True)
    )

    # Filtrar por campaña si se selecciona (por ForeignKey campania)
    if campania_id:
        try:
            cmp = CampaniaHistorial.objects.get(id=campania_id)
            # Buscar la campaña activa que corresponde a este historial
            campania_cfg = CampaniaConfig.objects.filter(inicio=cmp.inicio, fin=cmp.fin).first()
            if campania_cfg:
                reporte = reporte.filter(pedido__campania=campania_cfg)
            else:
                reporte = reporte.none()
        except CampaniaHistorial.DoesNotExist:
            reporte = reporte.none()

    # si hay búsqueda, filtramos
    if query:
        reporte = reporte.filter(Q(producto__sku__icontains=query) | Q(producto__descripcion__icontains=query))

    reporte = reporte.order_by("-num_pedidos")

    return render(
        request,
        "administrador/reporte_pedidos.html",
        {
            "reporte": reporte,
            "query": query,
            "campañas": campañas,
            "campania_id": campania_id,
        },
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
    from administrador.models import CampaniaHistorial
    empleado = get_object_or_404(Empleado, id=empleado_id)
    campania_id = request.GET.get("campania", "")
    campañas = CampaniaHistorial.objects.all().order_by("-inicio")

    pedidos = Pedido.objects.filter(empleado=empleado)
    if campania_id:
        try:
            cmp = CampaniaHistorial.objects.get(id=campania_id)
            campania_cfg = CampaniaConfig.objects.filter(inicio=cmp.inicio, fin=cmp.fin).first()
            if campania_cfg:
                pedidos = pedidos.filter(campania=campania_cfg)
            else:
                pedidos = pedidos.none()
        except CampaniaHistorial.DoesNotExist:
            pedidos = pedidos.none()
    pedidos = pedidos.prefetch_related("items__producto")

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
            "campañas": campañas,
            "campania_id": campania_id,
        },
    )


@login_required
@staff_required()
def lista_empleados_reporte(request):
    from administrador.models import CampaniaHistorial
    query = request.GET.get("q", "").strip()
    campania_id = request.GET.get("campania", "")
    campañas = CampaniaHistorial.objects.all().order_by("-inicio")  # Incluye todas

    empleados = Empleado.objects.all()
    if campania_id:
        try:
            campania = CampaniaHistorial.objects.get(id=campania_id)
            empleados = empleados.filter(
                pedidos__fecha__gte=campania.inicio,
                pedidos__fecha__lte=campania.fin
            ).distinct()
        except CampaniaHistorial.DoesNotExist:
            empleados = Empleado.objects.none()

    if query:
        empleados_por_nombre = Empleado.objects.filter(
            Q(preferred_name__icontains=query) | Q(sbd_email__icontains=query)
        )
        empleados_por_producto = Empleado.objects.filter(
            Q(pedidos__items__producto__descripcion__icontains=query)
            | Q(pedidos__items__producto__sku__icontains=query)
        )
        empleados = (empleados_por_nombre | empleados_por_producto | empleados).distinct()

    return render(
        request,
        "administrador/lista_empleados_reporte.html",
        {
            "empleados": empleados,
            "query": query,
            "campañas": campañas,
            "campania_id": campania_id,
        },
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


@login_required
@staff_required()
def generar_resumen_pedido(request, pedido_id):
    """Genera un resumen (PDF) para un pedido específico.

    Incluye: Nombre del empleado, correo, número de pedido, fecha/hora,
    y una tabla con: Código (SKU), Tipo de producto, Descripción, Cantidad, Precio unitario.
    """

    pedido = get_object_or_404(Pedido, id=pedido_id)
    empleado = pedido.empleado
    items = pedido.items.select_related("producto").all()

    # Respuesta PDF
    response = HttpResponse(content_type="application/pdf")
    filename = f"resumen_pedido_{pedido.id}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    margin_x = 50
    y = height - 50

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin_x, y, f"Resumen de pedido - {empleado.preferred_name}")
    y -= 24

    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin_x, y, f"Pedido #: {pedido.id}")
    pdf.drawString(margin_x + 180, y, f"Fecha: {pedido.fecha.strftime('%d/%m/%Y %H:%M')}")
    y -= 14
    pdf.drawString(margin_x, y, f"Correo: {empleado.sbd_email}")
    y -= 24

    # Tabla con columnas: Descripción | Referencia (SKU) | Tipo de producto | Precio (unitario x cantidad = total)
    pdf.setFont("Helvetica-Bold", 11)
    desc_x = margin_x + 5
    sku_x = margin_x + 210
    tipo_x = margin_x + 340
    precio_x = margin_x + 470

    # Encabezados alineados y sin solapamiento
    pdf.drawString(desc_x, y, "Descripción")
    pdf.drawString(sku_x, y, "Referencia (SKU)")
    pdf.drawString(tipo_x, y, "Tipo de producto")
    pdf.drawString(precio_x, y, "Precio")
    y -= 12
    pdf.line(margin_x, y, width - margin_x, y)
    y -= 14

    pdf.setFont("Helvetica", 10)
    total = 0
    for item in items:
        # salto de página si no cabe
        min_needed = 40
        if y < 80 + min_needed:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 10)

        desc = (item.producto.descripcion or "").replace("\n", " ")
        sku = item.producto.sku or ""
        tipo = item.producto.categoria or getattr(item.producto, "sbu", "") or ""
        cantidad = int(item.cantidad)
        precio_val = getattr(item.producto, "precio_sin_iva", None)
        precio_unit = float(precio_val) if precio_val is not None else 0
        precio_total = precio_unit * cantidad

        # Formato: $precio_unitario x cantidad = $precio_total
        if precio_val is not None:
            precio_str = f"${precio_unit:,.0f} x {cantidad}"
        else:
            precio_str = ""

        # Envolver la descripción en hasta 2 líneas para que quede presentable
        wrapped = textwrap.wrap(desc, width=55)
        line1 = wrapped[0] if len(wrapped) >= 1 else ""
        line2 = wrapped[1] if len(wrapped) >= 2 else None

        pdf.drawString(desc_x, y, line1)
        pdf.drawString(sku_x, y, sku)
        pdf.drawString(tipo_x, y, str(tipo)[:24])
        pdf.drawString(precio_x, y, precio_str)

        if line2:
            y -= 12
            pdf.drawString(desc_x, y, line2)

        # sumar total usando precio_sin_iva
        total += precio_total

        y -= 20

    # Línea separadora y total
    y -= 10
    pdf.line(margin_x, y, width - margin_x, y)
    y -= 18
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(width - margin_x, y, f"Valor total: ${total:,.2f}")

    pdf.showPage()
    pdf.save()

    return response


@login_required
@staff_required()
def exportar_resumen_empleados_pdf(request):
    from empleados.models import Empleado
    from productos.models import Pedido, PedidoItem
    from administrador.models import CampaniaHistorial

    query = request.GET.get("q", "").strip()
    campania_id = request.GET.get("campania", "")

    empleados = Empleado.objects.all()
    campania_hist = None
    campania_cfg = None
    if campania_id:
        try:
            campania_hist = CampaniaHistorial.objects.get(id=campania_id)
            # Intentar mapear al objeto CampaniaConfig creado con esas mismas fechas
            campania_cfg = CampaniaConfig.objects.filter(
                inicio=campania_hist.inicio,
                fin=campania_hist.fin,
            ).order_by("-id").first()
            if campania_cfg:
                empleados = empleados.filter(pedidos__campania=campania_cfg).distinct()
            else:
                # Respaldo por rango de fechas si no se encuentra la campaña exacta
                empleados = empleados.filter(
                    pedidos__fecha__gte=campania_hist.inicio,
                    pedidos__fecha__lte=campania_hist.fin,
                ).distinct()
        except CampaniaHistorial.DoesNotExist:
            empleados = Empleado.objects.none()

    if query:
        empleados_por_nombre = Empleado.objects.filter(
            Q(preferred_name__icontains=query) | Q(sbd_email__icontains=query)
        )
        empleados_por_producto = Empleado.objects.filter(
            Q(pedidos__items__producto__descripcion__icontains=query)
            | Q(pedidos__items__producto__sku__icontains=query)
        )
        empleados = (empleados_por_nombre | empleados_por_producto | empleados).distinct()

    # Preparar título y nombre de archivo según campaña
    if campania_hist:
        tz = timezone.get_current_timezone()
        ini = timezone.localtime(campania_hist.inicio, tz)
        fin = timezone.localtime(campania_hist.fin, tz)
        titulo_pdf = f"Resumen de campaña {ini.strftime('%d/%m/%Y %H:%M')} - {fin.strftime('%d/%m/%Y %H:%M')}"
        filename = f"resumen_campana_{ini.strftime('%Y%m%d_%H%M')}_a_{fin.strftime('%Y%m%d_%H%M')}.pdf"
    else:
        titulo_pdf = "Resumen general de pedidos"
        filename = "resumen_empleados.pdf"

    # Crear PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 40
    # Título principal del documento
    p.setTitle(titulo_pdf)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, titulo_pdf)
    y -= 30

    for empleado in empleados:
        pedidos = Pedido.objects.filter(empleado=empleado)
        # Filtrar solo los pedidos de la campaña seleccionada (preferir FK campania)
        if campania_cfg:
            pedidos = pedidos.filter(campania=campania_cfg)
        elif campania_hist:
            pedidos = pedidos.filter(fecha__gte=campania_hist.inicio, fecha__lte=campania_hist.fin)
        pedidos = pedidos.prefetch_related("items__producto")

        total_general = 0
        p.setFont("Helvetica-Bold", 14)
        p.drawString(40, y, f"Empleado: {empleado.preferred_name} ({empleado.sbd_email})")
        y -= 20
        p.setFont("Helvetica", 12)
        for pedido in pedidos:
            subtotal = sum(item.cantidad * item.producto.precio_sin_iva for item in pedido.items.all())
            p.drawString(60, y, f"Pedido #{pedido.id} - Fecha: {pedido.fecha.strftime('%d/%m/%Y %H:%M')}")
            y -= 16
            for item in pedido.items.all():
                p.drawString(80, y, f"{item.producto.descripcion} x {item.cantidad} - ${item.producto.precio_sin_iva}")
                y -= 14
            p.drawString(80, y, f"Subtotal: ${subtotal}")
            y -= 18
            total_general += subtotal
            y -= 6
            if y < 80:
                p.showPage()
                y = height - 40
                # Repetir título en nueva página
                p.setFont("Helvetica-Bold", 16)
                p.drawString(40, y, titulo_pdf)
                y -= 30
        p.setFont("Helvetica-Bold", 12)
        p.drawString(60, y, f"Total general: ${total_general}")
        y -= 30
        if y < 80:
            p.showPage()
            y = height - 40
            # Repetir título en nueva página
            p.setFont("Helvetica-Bold", 16)
            p.drawString(40, y, titulo_pdf)
            y -= 30
    p.save()
    return response


def staff_required():
    return user_passes_test(lambda u: u.is_staff)


@login_required
@staff_required()
def editar_politica_compra(request: HttpRequest) -> HttpResponse:
    """
    Pantalla para administrar la política de compra:
    - Subir/actualizar PDF
    - Agregar/editar enlace externo
    - Activar/desactivar
    """
    instancia = PoliticaCompra.objects.order_by("-actualizado").first()
    if not instancia:
        instancia = PoliticaCompra.objects.create(titulo="Política de compra de herramientas")

    if request.method == "POST":
        if "eliminar_pdf" in request.POST:
            if instancia.pdf:
                instancia.pdf.delete(save=False)
                instancia.pdf = None
                instancia.save()
                messages.success(request, "PDF eliminado. Puedes subir uno nuevo o usar solo el enlace.")
            else:
                messages.info(request, "No había PDF para eliminar.")
            return redirect("administrador:editar_politica_compra")

        form = PoliticaCompraForm(request.POST, request.FILES, instance=instancia)
        if form.is_valid():
            form.save()
            messages.success(request, "Política actualizada correctamente.")
            return redirect("administrador:editar_politica_compra")
    else:
        form = PoliticaCompraForm(instance=instancia)

    return render(
        request,
        "administrador/editar_politica_compra.html",
        {"form": form, "politica": instancia},
    )


@login_required
def dismiss_policy(request: HttpRequest) -> JsonResponse:
    """
    Marca en la sesión que ya se mostró el modal de política.
    (Si estás usando la versión con clave por versión en context processor,
     cambia esto por ese mecanismo.)
    """
    request.session["policy_shown"] = True
    request.session.modified = True
    return JsonResponse({"ok": True})


def _masinfo_singleton() -> MasInfo:
    obj = MasInfo.objects.order_by("-actualizado").first()
    if not obj:
        obj = MasInfo.objects.create(titulo="Más información")
    return obj


def masinfo_page(request):
    obj = MasInfo.objects.filter(activo=True).order_by("-actualizado").first()
    # Si no hay imagen activa, puedes renderizar un fallback o una página simple
    return render(request, "masinfo.html", {"masinfo": obj})


@login_required
@staff_required()
def editar_masinfo(request):
    obj = _masinfo_singleton()

    if request.method == "POST":
        if "eliminar_imagen" in request.POST:
            if obj.imagen:
                obj.imagen.delete(save=False)
                obj.imagen = None
                obj.save()
                messages.success(request, "Imagen eliminada. Puedes subir una nueva.")
            else:
                messages.info(request, "No había imagen para eliminar.")
            return redirect("administrador:editar_masinfo")

        form = MasInfoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "MásInfo actualizada correctamente.")
            return redirect("administrador:editar_masinfo")
    else:
        form = MasInfoForm(instance=obj)
    return render(request, "administrador/editar_masinfo.html", {"form": form, "masinfo": obj})

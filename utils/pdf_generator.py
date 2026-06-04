from pathlib import Path
import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import BASE_DIR, LOGO_FILE


BRAND_GOLD = colors.HexColor("#D99A19")
INK = colors.HexColor("#172033")
TEXT_MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#D8DEEA")
SOFT_BG = colors.HexColor("#F8FAFC")


def _money(value) -> str:
    return f"${float(value or 0):,.0f}"


def _text(value, fallback="No registra") -> str:
    value = "" if value is None else str(value).strip()
    return value or fallback


def _load_company_config() -> dict:
    config_path = BASE_DIR / "empresa_config.json"
    defaults = {
        "nombre": "Sueños Dorados",
        "nit": "000",
        "direccion": "",
        "ciudad": "",
        "contacto": "",
        "telefono": "",
        "actividad": "E-commerce textil",
    }
    try:
        with config_path.open("r", encoding="utf-8") as file:
            defaults.update(json.load(file))
    except Exception:
        pass
    return defaults


def _safe_paragraph(value, style):
    return Paragraph(_text(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def generate_invoice_pdf(order, output_dir="facturas") -> Path:
    """Genera una factura PDF para un pedido SQLAlchemy cargado con detalles."""
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    output_path.mkdir(parents=True, exist_ok=True)
    filename = output_path / f"factura_pedido_{order.id_pedido}.pdf"

    company = _load_company_config()
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BrandTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, textColor=INK, leading=26, spaceAfter=4))
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8.5, textColor=TEXT_MUTED, leading=11))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=INK, leading=12))
    styles.add(ParagraphStyle(name="Cell", parent=styles["Normal"], fontSize=8.5, textColor=INK, leading=10))

    logo = ""
    if LOGO_FILE.exists():
        try:
            logo = Image(str(LOGO_FILE), width=2.2 * cm, height=2.2 * cm)
        except Exception:
            logo = ""

    company_lines = [
        Paragraph(_text(company.get("nombre"), "Sueños Dorados"), styles["BrandTitle"]),
        Paragraph(_text(company.get("actividad"), "E-commerce textil"), styles["SmallMuted"]),
        Paragraph(f"NIT: {_text(company.get('nit'))}", styles["SmallMuted"]),
        Paragraph(f"{_text(company.get('direccion'))} - {_text(company.get('ciudad'))}", styles["SmallMuted"]),
        Paragraph(f"Tel: {_text(company.get('telefono'))} | Email: {_text(company.get('contacto'))}", styles["SmallMuted"]),
    ]
    header = Table(
        [[logo, company_lines, [Paragraph("FACTURA DE VENTA", styles["Label"]), Paragraph(f"No. {order.id_pedido:06d}", styles["BrandTitle"]), Paragraph(f"Fecha: {_text(order.fecha_pedido.strftime('%Y-%m-%d %H:%M') if order.fecha_pedido else '')}", styles["SmallMuted"])]]],
        colWidths=[2.5 * cm, 8.6 * cm, 6.0 * cm],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))

    user = getattr(order, "usuario", None)
    address = getattr(order, "direccion", None)
    state = getattr(order, "estado", None)
    payment = getattr(order, "pago", None)
    client_name = " ".join(part for part in [getattr(user, "nombre_usuario", ""), getattr(user, "apellido_usuario", "")] if part).strip()
    address_text = ", ".join(part for part in [
        getattr(address, "descripcion_direccion", ""),
        getattr(address, "descripcion_barrio", ""),
        getattr(address, "descripcion_municipio", ""),
        getattr(address, "descripcion_departamento", ""),
    ] if part)

    info = Table(
        [
            [Paragraph("Cliente", styles["Label"]), Paragraph("Entrega", styles["Label"]), Paragraph("Pedido", styles["Label"])],
            [
                Paragraph(f"{_text(client_name)}<br/>Correo: {_text(getattr(user, 'correo_electronico', None))}<br/>Telefono: {_text(getattr(user, 'telefono', None))}", styles["Cell"]),
                Paragraph(_text(address_text), styles["Cell"]),
                Paragraph(f"Estado: {_text(getattr(state, 'descripcion_estado', None))}<br/>Metodo de pago: {_text(getattr(payment, 'metodo_pago', None), 'Pendiente')}<br/>Fecha de pago: {_text(payment.fecha_pago.strftime('%Y-%m-%d %H:%M') if payment and payment.fecha_pago else '', 'Pendiente')}", styles["Cell"]),
            ],
        ],
        colWidths=[5.7 * cm, 6.2 * cm, 5.2 * cm],
    )
    info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SOFT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    rows = [["SKU", "Producto", "Detalle", "Cant.", "Precio unit.", "Subtotal"]]
    for detail in order.detalles:
        variant = detail.variante
        detail_parts = [
            getattr(getattr(variant, "medida", None), "nombre_medida", ""),
            getattr(getattr(variant, "color", None), "nombre_color", ""),
            getattr(variant, "referencia", ""),
        ]
        rows.append([
            _safe_paragraph(getattr(variant, "sku", ""), styles["Cell"]),
            _safe_paragraph(getattr(variant.producto, "nombre_producto", "Producto"), styles["Cell"]),
            _safe_paragraph(" / ".join(part for part in detail_parts if part), styles["Cell"]),
            str(detail.cantidad),
            _money(detail.precio_unitario),
            _money(detail.precio_unitario * detail.cantidad),
        ])

    items_table = Table(rows, colWidths=[3.0 * cm, 4.3 * cm, 3.7 * cm, 1.5 * cm, 2.3 * cm, 2.3 * cm], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT_BG]),
    ]))

    totals = Table(
        [
            ["Subtotal", _money(order.subtotal)],
            ["Descuento", f"- {_money(order.descuento)}"],
            ["Envio", _money(order.costo_envio)],
            ["Total", _money(order.total)],
        ],
        colWidths=[3.4 * cm, 3.2 * cm],
        hAlign="RIGHT",
    )
    totals.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("BACKGROUND", (0, -1), (-1, -1), BRAND_GOLD),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    story = [
        header,
        info,
        Spacer(1, 14),
        Paragraph("Detalle de compra", styles["Label"]),
        Spacer(1, 6),
        items_table,
        Spacer(1, 12),
        totals,
        Spacer(1, 14),
        Paragraph("Gracias por tu compra. Conserva este documento como soporte de la transaccion.", styles["SmallMuted"]),
    ]
    doc.build(story)
    return filename



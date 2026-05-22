from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_invoice_pdf(order, output_dir="facturas") -> Path:
    """Genera una factura PDF basica para un pedido SQLAlchemy cargado con detalles."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filename = output_path / f"factura_pedido_{order.id_pedido}.pdf"

    doc = SimpleDocTemplate(str(filename), pagesize=letter, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Sueños Dorados - Factura de venta", styles["Title"]),
        Paragraph("NIT 900.000.000-1", styles["Normal"]),
        Paragraph(f"Pedido #{order.id_pedido}", styles["Heading2"]),
        Spacer(1, 12),
    ]

    rows = [["SKU", "Producto", "Cantidad", "Precio", "Subtotal"]]
    for detail in order.detalles:
        variant = detail.variante
        rows.append([
            variant.sku,
            variant.producto.nombre_producto,
            str(detail.cantidad),
            f"${float(detail.precio_unitario):,.0f}",
            f"${float(detail.precio_unitario * detail.cantidad):,.0f}",
        ])
    rows.append(["", "", "", "Total", f"${float(order.total):,.0f}"])

    table = Table(rows, colWidths=[4 * cm, 5 * cm, 2 * cm, 3 * cm, 3 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(table)
    doc.build(story)
    return filename




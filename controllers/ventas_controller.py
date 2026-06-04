from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload

from models.catalogo_model import VarianteProducto
from models.inventario_model import MovimientoInventario
from models.ventas_model import DetallePedido, EstadoPedido, Pago, Pedido
from utils.pdf_generator import generate_invoice_pdf


class SalesController:
    def __init__(self, db: Session):
        self.db = db

    def daily_sales_total(self) -> Decimal:
        return self.db.query(func.coalesce(func.sum(Pedido.total), 0)).join(EstadoPedido).filter(
            func.date(Pedido.fecha_pedido) == func.current_date(),
            EstadoPedido.descripcion_estado.in_(["Pagado", "En preparación", "Despachado", "Entregado"]),
        ).scalar() or Decimal("0.00")

    def order_counts(self) -> dict:
        rows = (
            self.db.query(EstadoPedido.descripcion_estado, func.count(Pedido.id_pedido))
            .outerjoin(Pedido, Pedido.id_estado_pedido == EstadoPedido.id_estado_pedido)
            .group_by(EstadoPedido.descripcion_estado)
            .all()
        )
        counts = {name: count for name, count in rows}
        return {
            "pedidos": sum(counts.values()),
            "pendientes": counts.get("Pendiente", 0),
            "pagados": counts.get("Pagado", 0),
            "preparacion": counts.get("En preparación", 0),
        }

    def list_recent_orders(self, limit: int = 20):
        return (
            self.db.query(Pedido)
            .options(joinedload(Pedido.usuario), joinedload(Pedido.estado), joinedload(Pedido.detalles))
            .order_by(Pedido.fecha_pedido.desc())
            .limit(limit)
            .all()
        )

    def _ensure_kardex_table(self):
        self.db.execute(text("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id_movimiento SERIAL PRIMARY KEY,
                id_variante INT NOT NULL REFERENCES variantes_producto(id_variante) ON UPDATE CASCADE ON DELETE RESTRICT,
                tipo_movimiento VARCHAR(20) NOT NULL,
                cantidad INT NOT NULL,
                stock_anterior INT NOT NULL,
                stock_nuevo INT NOT NULL,
                referencia_documento VARCHAR(100),
                observacion TEXT,
                fecha_movimiento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))

    def discount_order_stock_once(self, pedido: Pedido) -> bool:
        referencia = f"PEDIDO-{pedido.id_pedido}"
        already_discounted = self.db.query(MovimientoInventario.id_movimiento).filter(
            MovimientoInventario.referencia_documento == referencia,
            MovimientoInventario.tipo_movimiento == "SALIDA",
        ).first()
        if already_discounted:
            return False

        for detalle in pedido.detalles:
            variant = self.db.execute(
                select(VarianteProducto)
                .where(VarianteProducto.id_variante == detalle.id_variante)
                .with_for_update()
            ).scalar_one()
            if variant.stock < detalle.cantidad:
                raise ValueError(f"Stock insuficiente para SKU {variant.sku}")

            stock_anterior = variant.stock
            variant.stock -= detalle.cantidad
            self.db.add(MovimientoInventario(
                id_variante=variant.id_variante,
                tipo_movimiento="SALIDA",
                cantidad=detalle.cantidad,
                stock_anterior=stock_anterior,
                stock_nuevo=variant.stock,
                referencia_documento=referencia,
                observacion="Salida automatica por pedido aprobado/despachado",
            ))
        return True

    def ensure_order_stock_discounted(self, pedido_id: int) -> bool:
        self._ensure_kardex_table()
        pedido = self.db.query(Pedido).filter(Pedido.id_pedido == pedido_id).with_for_update().one_or_none()
        if not pedido:
            raise ValueError("Pedido no encontrado")
        return self.discount_order_stock_once(pedido)

    def approve_payment(self, pedido_id: int, metodo_pago: str = "Bold", estado_destino: str = "Pagado") -> Pedido:
        """Aprueba o despacha un pedido, descuenta stock una sola vez y registra Kardex."""
        try:
            self._ensure_kardex_table()
            pedido = self.db.query(Pedido).filter(Pedido.id_pedido == pedido_id).with_for_update().one_or_none()
            if not pedido:
                raise ValueError("Pedido no encontrado")

            expected_subtotal = sum(det.cantidad * det.precio_unitario for det in pedido.detalles)
            if Decimal(expected_subtotal) != Decimal(pedido.subtotal):
                raise ValueError("El subtotal del pedido no coincide con el detalle")

            target_state = self.db.query(EstadoPedido).filter_by(descripcion_estado=estado_destino).one_or_none()
            if not target_state:
                raise ValueError(f"No existe el estado {estado_destino}")

            discounted = self.discount_order_stock_once(pedido)
            pedido.estado = target_state
            if not pedido.pago:
                self.db.add(Pago(id_pedido=pedido.id_pedido, monto=pedido.total, metodo_pago=metodo_pago))

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        pedido = (
            self.db.query(Pedido)
            .options(
                joinedload(Pedido.detalles)
                .joinedload(DetallePedido.variante)
                .joinedload(VarianteProducto.producto)
            )
            .filter(Pedido.id_pedido == pedido_id)
            .one()
        )
        if estado_destino == "Pagado" or discounted:
            generate_invoice_pdf(pedido)
        return pedido

from datetime import datetime
from decimal import Decimal

from models.catalogo_model import VarianteProducto
from models.inventario_model import MovimientoInventario
from models.ventas_model import DetallePedido, Pedido
from services.bold_payments_service import ESTADO_PENDIENTE, RESERVA_TEMPORAL, ensure_kardex_table


def create_order_with_stock_reservation(db, payload):
    items = payload["items"]
    if not items:
        raise ValueError("El carrito esta vacio")

    ensure_kardex_table(db)
    subtotal = Decimal("0.00")
    reserved = []

    for item in items:
        variant = (
            db.query(VarianteProducto)
            .filter(VarianteProducto.id_variante == int(item["id_variante"]))
            .with_for_update(of=VarianteProducto)
            .one_or_none()
        )
        if not variant or not variant.estado:
            raise ValueError(f"SKU no disponible: {item['id_variante']}")

        qty = int(item["cantidad"])
        if qty <= 0:
            raise ValueError("La cantidad debe ser mayor a cero")
        if int(variant.stock) < qty:
            raise ValueError(f"Stock insuficiente para SKU {variant.sku}")

        price = Decimal(str(item.get("precio_unitario") or variant.precio))
        previous_stock = int(variant.stock)
        variant.stock = previous_stock - qty
        subtotal += price * qty
        reserved.append((variant, qty, price, previous_stock, variant.stock))

    descuento = Decimal(str(payload.get("descuento", "0")))
    costo_envio = Decimal(str(payload.get("costo_envio", "0")))
    total = subtotal - descuento + costo_envio
    if total <= 0:
        raise ValueError("El total del pedido debe ser mayor a cero")

    order = Pedido(
        id_usuario=int(payload["id_usuario"]),
        id_direccion=int(payload["id_direccion"]),
        id_estado_pedido=ESTADO_PENDIENTE,
        fecha_pedido=datetime.utcnow(),
        subtotal=subtotal,
        descuento=descuento,
        costo_envio=costo_envio,
        total=total,
    )
    db.add(order)
    db.flush()

    reference = f"PEDIDO-{order.id_pedido}"
    for variant, qty, price, previous_stock, new_stock in reserved:
        db.add(DetallePedido(
            id_pedido=order.id_pedido,
            id_variante=variant.id_variante,
            cantidad=qty,
            precio_unitario=price,
        ))
        db.add(MovimientoInventario(
            id_variante=variant.id_variante,
            tipo_movimiento=RESERVA_TEMPORAL,
            cantidad=qty,
            stock_anterior=previous_stock,
            stock_nuevo=new_stock,
            referencia_documento=reference,
            observacion=f"Reserva temporal del pedido {order.id_pedido}",
        ))

    db.commit()
    return order

import json
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import text

from models.catalogo_model import VarianteProducto
from models.inventario_model import MovimientoInventario
from models.ventas_model import DetallePedido, Pago, Pedido, RespuestaBold

ESTADO_PENDIENTE = 1
ESTADO_PAGADO = 2
ESTADO_RECHAZADO = 6

RESERVA_TEMPORAL = "RESERVA_TEMPORAL"
VENTA_CONFIRMADA = "VENTA_CONFIRMADA"
DEVOLUCION_RESERVA = "DEVOLUCION_RESERVA"
EXPIRACION_RESERVA = "EXPIRACION_RESERVA"

REJECTED_STATUSES = {"REJECTED", "FAILED", "CANCELLED", "CANCELED"}


def ensure_kardex_table(db):
    db.execute(text("""
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
    db.execute(text("ALTER TABLE movimientos_inventario ALTER COLUMN fecha_movimiento SET DEFAULT CURRENT_TIMESTAMP"))


def _order_reference(order_id):
    return f"PEDIDO-{order_id}"


def _has_release_movement(db, order_id):
    return db.execute(
        text("""
            SELECT 1
            FROM movimientos_inventario
            WHERE referencia_documento = :reference
              AND tipo_movimiento IN (:devolucion, :expiracion)
            LIMIT 1
        """),
        {
            "reference": _order_reference(order_id),
            "devolucion": DEVOLUCION_RESERVA,
            "expiracion": EXPIRACION_RESERVA,
        },
    ).first() is not None


def _lock_order(db, order_id):
    return (
        db.query(Pedido)
        .filter(Pedido.id_pedido == int(order_id))
        .with_for_update(of=Pedido)
        .one_or_none()
    )


def _lock_order_details(db, order_id):
    return (
        db.query(DetallePedido)
        .filter(DetallePedido.id_pedido == int(order_id))
        .with_for_update(of=DetallePedido)
        .all()
    )


def _lock_variant(db, variant_id):
    return (
        db.query(VarianteProducto)
        .filter(VarianteProducto.id_variante == int(variant_id))
        .with_for_update(of=VarianteProducto)
        .one()
    )


def _record_bold_response(db, order_id, transaction_id, status, payment_method, amount, raw_payload):
    response = RespuestaBold(
        id_pedido=order_id,
        transaction_id=transaction_id,
        status=status,
        payment_method=payment_method,
        amount=amount,
        timestamp_bold=datetime.utcnow(),
        raw_response=json.dumps(raw_payload, ensure_ascii=False),
    )
    db.add(response)
    db.flush()
    return response


def _release_reserved_stock(db, order, movement_type):
    if _has_release_movement(db, order.id_pedido):
        return False

    details = _lock_order_details(db, order.id_pedido)
    for detail in details:
        variant = _lock_variant(db, detail.id_variante)
        previous_stock = int(variant.stock)
        variant.stock = previous_stock + int(detail.cantidad)
        db.add(MovimientoInventario(
            id_variante=variant.id_variante,
            tipo_movimiento=movement_type,
            cantidad=detail.cantidad,
            stock_anterior=previous_stock,
            stock_nuevo=variant.stock,
            referencia_documento=_order_reference(order.id_pedido),
            observacion=f"Devolucion de reserva del pedido {order.id_pedido}",
        ))
    return True


def process_bold_payment(db, payload, raw_payload=None):
    transaction_id = payload["transaction_id"]
    order_id = int(payload["order_id"])
    bold_status = str(payload["status"]).upper()
    amount = Decimal(str(payload["amount"]))
    payment_method = payload.get("payment_method") or "Bold"
    raw_payload = raw_payload or payload

    ensure_kardex_table(db)
    existing_response = db.query(RespuestaBold).filter(RespuestaBold.transaction_id == transaction_id).one_or_none()
    if existing_response:
        return {
            "ok": True,
            "message": "Transaccion ya procesada previamente",
            "order_id": existing_response.id_pedido,
            "transaction_id": transaction_id,
            "idempotent": True,
        }

    order = _lock_order(db, order_id)
    if not order:
        raise ValueError("Pedido no encontrado")

    response = _record_bold_response(db, order.id_pedido, transaction_id, bold_status, payment_method, amount, raw_payload)

    if amount != Decimal(order.total):
        order.id_estado_pedido = ESTADO_RECHAZADO
        _release_reserved_stock(db, order, DEVOLUCION_RESERVA)
        db.commit()
        return {
            "ok": False,
            "message": "Monto invalido; pedido rechazado y reserva devuelta",
            "order_id": order.id_pedido,
            "transaction_id": transaction_id,
            "idempotent": False,
        }

    if bold_status == "APPROVED":
        existing_payment = (
            db.query(Pago)
            .filter(Pago.id_pedido == order.id_pedido)
            .with_for_update(of=Pago)
            .one_or_none()
        )
        if not existing_payment:
            db.add(Pago(
                id_pedido=order.id_pedido,
                id_respuesta_bold=response.id_respuesta,
                monto=amount,
                metodo_pago=payment_method,
            ))
        db.execute(
            text("""
                UPDATE movimientos_inventario
                SET tipo_movimiento = :confirmed,
                    observacion = :observation
                WHERE referencia_documento = :reference
                  AND tipo_movimiento = :reserved
            """),
            {
                "confirmed": VENTA_CONFIRMADA,
                "reserved": RESERVA_TEMPORAL,
                "reference": _order_reference(order.id_pedido),
                "observation": f"Venta confirmada por Bold: {transaction_id}",
            },
        )
        order.id_estado_pedido = ESTADO_PAGADO
        db.commit()
        return {
            "ok": True,
            "message": "Pago aprobado y reserva confirmada",
            "order_id": order.id_pedido,
            "transaction_id": transaction_id,
            "idempotent": False,
        }

    if bold_status in REJECTED_STATUSES:
        order.id_estado_pedido = ESTADO_RECHAZADO
        released = _release_reserved_stock(db, order, DEVOLUCION_RESERVA)
        db.commit()
        message = "Pago rechazado; reserva devuelta al inventario" if released else "Pago rechazado; la reserva ya habia sido devuelta"
        return {
            "ok": True,
            "message": message,
            "order_id": order.id_pedido,
            "transaction_id": transaction_id,
            "idempotent": False,
        }

    db.rollback()
    raise ValueError(f"Estado Bold no soportado: {bold_status}")


def expire_pending_reservations(db, minutes=20):
    ensure_kardex_table(db)
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    orders = (
        db.query(Pedido)
        .filter(Pedido.id_estado_pedido == ESTADO_PENDIENTE, Pedido.fecha_pedido <= cutoff)
        .with_for_update(of=Pedido)
        .all()
    )
    expired = []
    for order in orders:
        has_bold_response = db.query(RespuestaBold).filter(RespuestaBold.id_pedido == order.id_pedido).first()
        if has_bold_response:
            continue
        order.id_estado_pedido = ESTADO_RECHAZADO
        _release_reserved_stock(db, order, EXPIRACION_RESERVA)
        expired.append(order.id_pedido)
    db.commit()
    return expired

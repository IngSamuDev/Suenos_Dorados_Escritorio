from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.crud import register_crud_routes
from api.serialization import model_to_dict
from database import get_db
from models.ventas_model import DetallePedido, EstadoPedido, Pago, Pedido, RespuestaBold

router = APIRouter(prefix="/api/admin/sales", tags=["sales"])


@router.get("/orders-by-status")
def orders_by_status(db: Session = Depends(get_db)):
    rows = (
        db.query(EstadoPedido.descripcion_estado, func.count(Pedido.id_pedido))
        .outerjoin(Pedido, Pedido.id_estado_pedido == EstadoPedido.id_estado_pedido)
        .group_by(EstadoPedido.descripcion_estado)
        .all()
    )
    return [{"estado": estado, "total": total} for estado, total in rows]


@router.get("/recent-orders")
def recent_orders(db: Session = Depends(get_db)):
    orders = db.query(Pedido).order_by(Pedido.fecha_pedido.desc()).limit(20).all()
    return [model_to_dict(order) for order in orders]


register_crud_routes(router, "/orders", Pedido, "id_pedido")
register_crud_routes(router, "/order-details", DetallePedido, "id_detalle_pedido")
register_crud_routes(router, "/order-statuses", EstadoPedido, "id_estado_pedido")
register_crud_routes(router, "/payments", Pago, "id_pago")
register_crud_routes(router, "/bold-responses", RespuestaBold, "id_respuesta")



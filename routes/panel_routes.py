from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.catalogo_model import Categoria, Coleccion, Producto, VarianteProducto
from models.ventas_model import EstadoPedido, Pedido
from models.usuarios_model import Usuario

router = APIRouter(prefix="/api/admin/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    active_variant = VarianteProducto.estado.is_(True)
    paid_states = ["Pagado", "En preparacion", "En preparación", "Despachado", "Entregado"]
    return {
        "usuarios": db.query(func.count(Usuario.id_usuario)).scalar() or 0,
        "productos": db.query(func.count(Producto.id_producto)).filter(Producto.estado_producto.is_(True)).scalar() or 0,
        "categorias": db.query(func.count(Categoria.id_categoria)).scalar() or 0,
        "colecciones": db.query(func.count(Coleccion.id_coleccion)).filter(Coleccion.estado.is_(True)).scalar() or 0,
        "variantes": db.query(func.count(VarianteProducto.id_variante)).filter(active_variant).scalar() or 0,
        "stock_total": db.query(func.coalesce(func.sum(VarianteProducto.stock), 0)).filter(active_variant).scalar() or 0,
        "stock_bajo": db.query(func.count(VarianteProducto.id_variante)).filter(active_variant, VarianteProducto.stock > 0, VarianteProducto.stock <= 3).scalar() or 0,
        "agotados": db.query(func.count(VarianteProducto.id_variante)).filter(active_variant, VarianteProducto.stock <= 0).scalar() or 0,
        "valor_inventario": float(db.query(func.coalesce(func.sum(VarianteProducto.precio * VarianteProducto.stock), 0)).filter(active_variant).scalar() or 0),
        "pedidos": db.query(func.count(Pedido.id_pedido)).scalar() or 0,
        "ventas_hoy": float(
            db.query(func.coalesce(func.sum(Pedido.total), 0))
            .join(EstadoPedido)
            .filter(func.date(Pedido.fecha_pedido) == func.current_date(), EstadoPedido.descripcion_estado.in_(paid_states))
            .scalar()
            or 0
        ),
    }



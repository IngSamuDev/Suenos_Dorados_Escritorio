from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.crud import register_crud_routes
from api.serialization import model_to_dict
from database import get_db
from models.catalogo_model import VarianteProducto
from models.inventario_model import MovimientoInventario

router = APIRouter(prefix="/api/admin/inventory", tags=["inventory"])


@router.get("/metrics")
def inventory_metrics(db: Session = Depends(get_db)):
    active_variant = VarianteProducto.estado.is_(True)
    return {
        "stock_total": db.query(func.coalesce(func.sum(VarianteProducto.stock), 0)).filter(active_variant).scalar() or 0,
        "stock_bajo": db.query(func.count(VarianteProducto.id_variante)).filter(active_variant, VarianteProducto.stock > 0, VarianteProducto.stock <= 3).scalar() or 0,
        "agotados": db.query(func.count(VarianteProducto.id_variante)).filter(active_variant, VarianteProducto.stock <= 0).scalar() or 0,
        "valor_inventario": float(db.query(func.coalesce(func.sum(VarianteProducto.precio * VarianteProducto.stock), 0)).filter(active_variant).scalar() or 0),
    }


@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db)):
    variants = (
        db.query(VarianteProducto)
        .filter(VarianteProducto.estado.is_(True), VarianteProducto.stock > 0, VarianteProducto.stock <= 3)
        .order_by(VarianteProducto.stock.asc(), VarianteProducto.sku.asc())
        .all()
    )
    return [model_to_dict(variant) for variant in variants]


register_crud_routes(router, "/variants", VarianteProducto, "id_variante")
register_crud_routes(router, "/movements", MovimientoInventario, "id_movimiento")



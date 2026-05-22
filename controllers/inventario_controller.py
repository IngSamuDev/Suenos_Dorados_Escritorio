from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.catalogo_model import Producto, VarianteProducto


LOW_STOCK_THRESHOLD = 3


class InventoryController:
    def __init__(self, db: Session, low_stock_threshold: int = LOW_STOCK_THRESHOLD):
        self.db = db
        self.low_stock_threshold = low_stock_threshold

    def list_stock(self):
        return (
            self.db.query(VarianteProducto)
            .options(
                joinedload(VarianteProducto.producto).joinedload(Producto.categoria),
                joinedload(VarianteProducto.medida),
                joinedload(VarianteProducto.color),
            )
            .filter(VarianteProducto.estado.is_(True))
            .order_by(VarianteProducto.stock.asc(), VarianteProducto.sku.asc())
            .all()
        )
    def low_stock_variants(self):
        return (
            self.db.query(VarianteProducto)
            .options(joinedload(VarianteProducto.producto), joinedload(VarianteProducto.medida))
            .filter(
                VarianteProducto.estado.is_(True),
                VarianteProducto.stock > 0,
                VarianteProducto.stock <= self.low_stock_threshold,
            )
            .order_by(VarianteProducto.stock.asc(), VarianteProducto.sku.asc())
            .all()
        )

    def out_of_stock_variants(self):
        return (
            self.db.query(VarianteProducto)
            .options(joinedload(VarianteProducto.producto), joinedload(VarianteProducto.medida))
            .filter(VarianteProducto.estado.is_(True), VarianteProducto.stock <= 0)
            .order_by(VarianteProducto.sku.asc())
            .all()
        )

    def inventory_summary(self) -> dict:
        active = VarianteProducto.estado.is_(True)
        return {
            "stock_total": self.db.query(func.coalesce(func.sum(VarianteProducto.stock), 0)).filter(active).scalar() or 0,
            "stock_bajo": self.db.query(func.count(VarianteProducto.id_variante)).filter(active, VarianteProducto.stock > 0, VarianteProducto.stock <= self.low_stock_threshold).scalar() or 0,
            "agotados": self.db.query(func.count(VarianteProducto.id_variante)).filter(active, VarianteProducto.stock <= 0).scalar() or 0,
            "valor_inventario": float(self.db.query(func.coalesce(func.sum(VarianteProducto.precio * VarianteProducto.stock), 0)).filter(active).scalar() or 0),
        }

    def stock_status(self, variant: VarianteProducto) -> str:
        if variant.stock <= 0:
            return "Agotado"
        if variant.stock <= self.low_stock_threshold:
            return "Stock bajo"
        return "Normal"






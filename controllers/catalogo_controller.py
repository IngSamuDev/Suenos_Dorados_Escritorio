from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.catalogo_model import Categoria, Coleccion, Producto, VarianteProducto


class CatalogController:
    def __init__(self, db: Session):
        self.db = db

    def list_products(self):
        return (
            self.db.query(Producto)
            .options(joinedload(Producto.categoria), joinedload(Producto.coleccion), joinedload(Producto.variantes))
            .order_by(Producto.nombre_producto.asc())
            .all()
        )

    def create_product(self, data: dict) -> Producto:
        product = Producto(**data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, data: dict) -> Producto:
        product = self.db.get(Producto, product_id)
        if not product:
            raise ValueError("Producto no encontrado")
        for field, value in data.items():
            setattr(product, field, value)
        self.db.commit()
        self.db.refresh(product)
        return product

    def toggle_product_visibility(self, product_id: int, visible: bool) -> Producto:
        return self.update_product(product_id, {"estado_producto": visible})

    def delete_product(self, product_id: int) -> None:
        product = self.db.get(Producto, product_id)
        if not product:
            raise ValueError("Producto no encontrado")
        self.db.delete(product)
        self.db.commit()

    def list_categories(self):
        return self.db.query(Categoria).order_by(Categoria.nombre_categoria.asc()).all()

    def list_collections(self):
        return self.db.query(Coleccion).order_by(Coleccion.nombre_coleccion.asc()).all()

    def dashboard_counts(self) -> dict:
        return {
            "productos": self.db.query(func.count(Producto.id_producto)).filter(Producto.estado_producto.is_(True)).scalar() or 0,
            "categorias": self.db.query(func.count(Categoria.id_categoria)).scalar() or 0,
            "colecciones": self.db.query(func.count(Coleccion.id_coleccion)).filter(Coleccion.estado.is_(True)).scalar() or 0,
            "variantes": self.db.query(func.count(VarianteProducto.id_variante)).filter(VarianteProducto.estado.is_(True)).scalar() or 0,
        }



from datetime import date
from decimal import Decimal

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from models.catalogo_model import Producto, VarianteProducto
from models.descuentos_model import Descuento
from controllers.crud_base_controller import BaseCrudController


class DiscountController:
    def __init__(self, db: Session):
        self.db = db

    def list_discounts(self):
        return (
            self.db.query(Descuento)
            .options(joinedload(Descuento.producto))
            .order_by(desc(Descuento.id))
            .all()
        )

    def get_discount(self, discount_id: int) -> Descuento:
        discount = self.db.get(Descuento, discount_id)
        if not discount:
            raise ValueError("Descuento no encontrado")
        return discount

    def create_discount(self, data: dict) -> Descuento:
        discount = Descuento(**data)
        self.db.add(discount)
        self.db.commit()
        self.db.refresh(discount)
        return discount

    def update_discount(self, discount_id: int, data: dict) -> Descuento:
        discount = self.get_discount(discount_id)
        for field, value in data.items():
            setattr(discount, field, value)
        self.db.commit()
        self.db.refresh(discount)
        return discount

    def delete_discount(self, discount_id: int) -> Descuento:
        discount = self.get_discount(discount_id)
        self.db.delete(discount)
        self.db.commit()
        return discount

    def active_discount_for_product(self, product_id: int, current_date: date | None = None) -> Descuento | None:
        current_date = current_date or date.today()
        return (
            self.db.query(Descuento)
            .filter(
                Descuento.id_producto == product_id,
                Descuento.is_active.is_(True),
                Descuento.fecha_inicio <= current_date,
                Descuento.fecha_fin >= current_date,
            )
            .order_by(Descuento.porcentaje_descuento.desc(), Descuento.id.desc())
            .first()
        )

    def product_with_discount_prices(self, product_id: int) -> dict:
        product = (
            self.db.query(Producto)
            .options(joinedload(Producto.variantes), joinedload(Producto.descuentos))
            .filter(Producto.id_producto == product_id)
            .first()
        )
        if not product:
            raise ValueError("Producto no encontrado")

        discount = self.active_discount_for_product(product.id_producto)
        percentage = Decimal(discount.porcentaje_descuento) if discount else Decimal("0")

        return {
            "id_producto": product.id_producto,
            "nombre_producto": product.nombre_producto,
            "slug": product.slug,
            "estado_producto": product.estado_producto,
            "descuento_activo": {
                "id": discount.id,
                "codigo": discount.codigo,
                "porcentaje_descuento": float(discount.porcentaje_descuento),
                "fecha_inicio": discount.fecha_inicio.isoformat(),
                "fecha_fin": discount.fecha_fin.isoformat(),
            }
            if discount
            else None,
            "variantes": [self.variant_price_payload(variant, percentage) for variant in product.variantes],
        }

    @staticmethod
    def variant_price_payload(variant: VarianteProducto, percentage: Decimal) -> dict:
        price = Decimal(variant.precio or 0)
        final_price = price * (Decimal("1") - (percentage / Decimal("100")))
        return {
            "id_variante": variant.id_variante,
            "sku": variant.sku,
            "referencia": variant.referencia,
            "precio": float(price),
            "porcentaje_descuento": float(percentage),
            "precio_final_con_descuento": float(final_price.quantize(Decimal("0.01"))),
            "stock": variant.stock,
            "estado": variant.estado,
        }

    def discounts_count(self) -> int:
        return self.db.query(func.count(Descuento.id)).scalar() or 0


class DescuentosController(BaseCrudController):
    """Controlador del CRUD administrativo de descuentos."""

    group_id = "descuentos"



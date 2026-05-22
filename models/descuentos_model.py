from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Descuento(Base):
    __tablename__ = "descuentos"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_descuentos_codigo"),
        CheckConstraint("porcentaje_descuento >= 0 AND porcentaje_descuento <= 100", name="ck_descuentos_porcentaje_rango"),
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_descuentos_fechas_validas"),
        Index("ix_descuentos_producto_activo", "id_producto", "is_active"),
        Index("ix_descuentos_codigo_activo", "codigo", "is_active"),
    )

    id = Column(Integer, primary_key=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto", onupdate="CASCADE", ondelete="SET NULL"))
    codigo = Column(String(40), nullable=False)
    porcentaje_descuento = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    fecha_inicio = Column(Date, nullable=False, default=date.today)
    fecha_fin = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    producto = relationship("Producto", back_populates="descuentos")

    def esta_vigente(self, fecha: date | None = None) -> bool:
        fecha = fecha or date.today()
        return bool(self.is_active and self.fecha_inicio <= fecha <= self.fecha_fin)



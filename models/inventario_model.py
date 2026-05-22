from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class MovimientoInventario(Base):
    """Extension recomendada para Kardex; requiere migracion antes de usarla."""

    __tablename__ = "movimientos_inventario"

    id_movimiento = Column(Integer, primary_key=True)
    id_variante = Column(Integer, ForeignKey("variantes_producto.id_variante", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    tipo_movimiento = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)
    stock_anterior = Column(Integer, nullable=False)
    stock_nuevo = Column(Integer, nullable=False)
    referencia_documento = Column(String(100))
    observacion = Column(Text)
    fecha_movimiento = Column(DateTime, nullable=False, default=datetime.utcnow)

    variante = relationship("VarianteProducto")



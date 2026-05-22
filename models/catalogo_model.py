from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria = Column(Integer, primary_key=True)
    nombre_categoria = Column(String(80), nullable=False)
    descripcion_categoria = Column(Text)
    slug = Column(String(100), nullable=False, unique=True)

    colecciones = relationship("Coleccion", back_populates="categoria")
    productos = relationship("Producto", back_populates="categoria")


class Coleccion(Base):
    __tablename__ = "colecciones"

    id_coleccion = Column(Integer, primary_key=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    nombre_coleccion = Column(String(100), nullable=False)
    descripcion_coleccion = Column(Text)
    estado = Column(Boolean, nullable=False, default=True)

    categoria = relationship("Categoria", back_populates="colecciones")
    productos = relationship("Producto", back_populates="coleccion")


class Color(Base):
    __tablename__ = "colores"

    id_color = Column(Integer, primary_key=True)
    nombre_color = Column(String(60), nullable=False)
    codigo_hex = Column(String(7))

    variantes = relationship("VarianteProducto", back_populates="color")
    imagenes = relationship("ImagenProducto", back_populates="color")


class Medida(Base):
    __tablename__ = "medidas"

    id_medida = Column(Integer, primary_key=True)
    nombre_medida = Column(String(50), nullable=False)
    ancho_cm = Column(Numeric(6, 2))
    largo_cm = Column(Numeric(6, 2))
    descripcion = Column(String(100))

    variantes = relationship("VarianteProducto", back_populates="medida")


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        Index("ix_productos_categoria_estado", "id_categoria", "estado_producto"),
        Index("ix_productos_coleccion_estado", "id_coleccion", "estado_producto"),
    )

    id_producto = Column(Integer, primary_key=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    id_coleccion = Column(Integer, ForeignKey("colecciones.id_coleccion", onupdate="CASCADE", ondelete="SET NULL"))
    nombre_producto = Column(String(150), nullable=False)
    descripcion_producto = Column(Text)
    slug = Column(String(180), nullable=False, unique=True)
    estado_producto = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)

    categoria = relationship("Categoria", back_populates="productos")
    coleccion = relationship("Coleccion", back_populates="productos")
    variantes = relationship("VarianteProducto", back_populates="producto", cascade="all, delete-orphan")
    imagenes = relationship("ImagenProducto", back_populates="producto", cascade="all, delete-orphan")
    descuentos = relationship("Descuento", back_populates="producto")


class VarianteProducto(Base):
    __tablename__ = "variantes_producto"
    __table_args__ = (
        UniqueConstraint("id_producto", "id_medida", "id_color", "referencia", name="uq_variantes_combinacion"),
        Index("ix_variantes_estado_stock", "estado", "stock"),
        Index("ix_variantes_producto_estado", "id_producto", "estado"),
    )

    id_variante = Column(Integer, primary_key=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    id_medida = Column(Integer, ForeignKey("medidas.id_medida", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    id_color = Column(Integer, ForeignKey("colores.id_color", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    sku = Column(String(60), nullable=False, unique=True)
    precio = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    referencia = Column(String(100), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    estado = Column(Boolean, nullable=False, default=True)

    producto = relationship("Producto", back_populates="variantes")
    medida = relationship("Medida", back_populates="variantes")
    color = relationship("Color", back_populates="variantes")
    detalles_pedido = relationship("DetallePedido", back_populates="variante")

    @property
    def agotado(self) -> bool:
        return self.stock <= 0


class ImagenProducto(Base):
    __tablename__ = "imagenes_producto"

    id_imagen = Column(Integer, primary_key=True)
    id_producto = Column(Integer, ForeignKey("productos.id_producto", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    id_color = Column(Integer, ForeignKey("colores.id_color", onupdate="CASCADE", ondelete="SET NULL"))
    url_imagen = Column(String(500), nullable=False)
    orden = Column(Integer, nullable=False, default=1)
    es_principal = Column(Boolean, nullable=False, default=False)

    producto = relationship("Producto", back_populates="imagenes")
    color = relationship("Color", back_populates="imagenes")



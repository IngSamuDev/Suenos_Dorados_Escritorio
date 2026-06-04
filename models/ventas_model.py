from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Direccion(Base):
    __tablename__ = "direcciones"

    id_direccion = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    descripcion_direccion = Column(String(200), nullable=False)
    descripcion_barrio = Column(String(100))
    descripcion_municipio = Column(String(100), nullable=False)
    descripcion_departamento = Column(String(100), nullable=False)
    es_principal = Column(Boolean, nullable=False, default=False)

    usuario = relationship("Usuario", back_populates="direcciones")
    pedidos = relationship("Pedido", back_populates="direccion")


class EstadoPedido(Base):
    __tablename__ = "estado_pedido"

    id_estado_pedido = Column(Integer, primary_key=True)
    descripcion_estado = Column(String(60), nullable=False)

    pedidos = relationship("Pedido", back_populates="estado")


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        Index("ix_pedidos_estado_fecha", "id_estado_pedido", "fecha_pedido"),
        Index("ix_pedidos_usuario_fecha", "id_usuario", "fecha_pedido"),
    )

    id_pedido = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    id_direccion = Column(Integer, ForeignKey("direcciones.id_direccion", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    id_estado_pedido = Column(Integer, ForeignKey("estado_pedido.id_estado_pedido", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    fecha_pedido = Column(DateTime, nullable=False, default=datetime.utcnow)
    subtotal = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    descuento = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    costo_envio = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    usuario = relationship("Usuario", back_populates="pedidos")
    direccion = relationship("Direccion", back_populates="pedidos")
    estado = relationship("EstadoPedido", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    pago = relationship("Pago", back_populates="pedido", uselist=False)
    envio = relationship("Envio", back_populates="pedido", uselist=False)


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id_detalle_pedido = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    id_variante = Column(Integer, ForeignKey("variantes_producto.id_variante", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="detalles")
    variante = relationship("VarianteProducto", back_populates="detalles_pedido")


class RespuestaBold(Base):
    __tablename__ = "respuesta_bold"

    id_respuesta = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    transaction_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(30), nullable=False)
    payment_method = Column(String(50))
    amount = Column(Numeric(12, 2), nullable=False)
    timestamp_bold = Column(DateTime, nullable=False)
    raw_response = Column(Text)

    pagos = relationship("Pago", back_populates="respuesta_bold")


class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, unique=True)
    id_respuesta_bold = Column(Integer, ForeignKey("respuesta_bold.id_respuesta", onupdate="CASCADE", ondelete="SET NULL"))
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_pago = Column(DateTime, nullable=False, default=datetime.utcnow)
    metodo_pago = Column(String(50), nullable=False)

    pedido = relationship("Pedido", back_populates="pago")
    respuesta_bold = relationship("RespuestaBold", back_populates="pagos")


class EstadoEnvio(Base):
    __tablename__ = "estado_envio"

    id_estado_envio = Column(Integer, primary_key=True)
    descripcion_estado = Column(String(60), nullable=False)

    envios = relationship("Envio", back_populates="estado")


class Envio(Base):
    __tablename__ = "envio"

    id_envio = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id_pedido", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False, unique=True)
    id_estado_envio = Column(Integer, ForeignKey("estado_envio.id_estado_envio", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    numero_guia = Column(String(100), unique=True)
    transportadora = Column(String(80))
    fecha_envio = Column(DateTime)
    fecha_entrega_estimada = Column(DateTime)
    fecha_entrega_real = Column(DateTime)

    pedido = relationship("Pedido", back_populates="envio")
    estado = relationship("EstadoEnvio", back_populates="envios")





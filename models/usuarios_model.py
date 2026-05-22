from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True)
    descripcion_rol = Column(String(50), nullable=False)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        Index("ix_usuarios_id_rol_estado", "id_rol", "estado"),
    )

    id_usuario = Column(Integer, primary_key=True)
    id_rol = Column(Integer, ForeignKey("roles.id_rol", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    nombre_usuario = Column(String(80), nullable=False)
    apellido_usuario = Column(String(80), nullable=False)
    correo_electronico = Column(String(120), nullable=False, unique=True)
    telefono = Column(String(20))
    contrasena_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    estado = Column(Boolean, nullable=False, default=True)

    rol = relationship("Rol", back_populates="usuarios")
    direcciones = relationship("Direccion", back_populates="usuario")
    pedidos = relationship("Pedido", back_populates="usuario")




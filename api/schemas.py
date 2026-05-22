from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DescuentoBase(BaseModel):
    id_producto: int | None = None
    codigo: str = Field(min_length=2, max_length=40)
    porcentaje_descuento: Decimal = Field(ge=0, le=100)
    fecha_inicio: date
    fecha_fin: date
    is_active: bool = True

    @field_validator("codigo")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("fecha_fin")
    @classmethod
    def validate_dates(cls, value: date, info):
        fecha_inicio = info.data.get("fecha_inicio")
        if fecha_inicio and value < fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return value


class DescuentoCreate(DescuentoBase):
    pass


class DescuentoUpdate(BaseModel):
    id_producto: int | None = None
    codigo: str | None = Field(default=None, min_length=2, max_length=40)
    porcentaje_descuento: Decimal | None = Field(default=None, ge=0, le=100)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    is_active: bool | None = None

    @field_validator("codigo")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else value


class DescuentoResponse(DescuentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class VariantePrecioDescuentoResponse(BaseModel):
    id_variante: int
    sku: str
    referencia: str
    precio: float
    porcentaje_descuento: float
    precio_final_con_descuento: float
    stock: int
    estado: bool


class ProductoConDescuentoResponse(BaseModel):
    id_producto: int
    nombre_producto: str
    slug: str
    estado_producto: bool
    descuento_activo: dict | None
    variantes: list[VariantePrecioDescuentoResponse]



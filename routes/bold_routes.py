import base64
import hashlib
import hmac
import os
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models.catalogo_model import VarianteProducto
from models.ventas_model import DetallePedido, Pedido
from services.bold_payments_service import expire_pending_reservations, process_bold_payment
from services.checkout_service import create_order_with_stock_reservation

router = APIRouter(tags=["bold-payments"])

class BoldWebhookPayload(BaseModel):
    transaction_id: str = Field(min_length=4, max_length=100)
    order_id: int = Field(gt=0)
    status: str = Field(pattern="^(APPROVED|REJECTED|FAILED|CANCELLED|CANCELED)$")
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(default="Bold", max_length=50)


class CheckoutItemPayload(BaseModel):
    id_variante: int = Field(gt=0)
    cantidad: int = Field(gt=0)
    precio_unitario: Decimal | None = Field(default=None, gt=0)


class CreateCheckoutOrderPayload(BaseModel):
    id_usuario: int = Field(gt=0)
    id_direccion: int = Field(gt=0)
    items: list[CheckoutItemPayload] = Field(min_length=1)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    costo_envio: Decimal = Field(default=Decimal("0.00"), ge=0)


class CreateCheckoutOrderResponse(BaseModel):
    ok: bool
    order_id: int
    total: Decimal
    message: str


class ExpireReservationsPayload(BaseModel):
    minutes: int = Field(default=20, ge=1, le=1440)


class ExpireReservationsResponse(BaseModel):
    ok: bool
    expired_order_ids: list[int]
    message: str


class OrderDetailResponse(BaseModel):
    sku: str
    producto: str
    cantidad: int
    precio_unitario: Decimal


class OrderResponse(BaseModel):
    id_pedido: int
    cliente: str
    total: Decimal
    id_estado_pedido: int
    estado: str
    pago_status: str
    detalles: list[OrderDetailResponse]


class WebhookResponse(BaseModel):
    ok: bool
    message: str
    order_id: int | None = None
    transaction_id: str
    idempotent: bool = False


def _validate_webhook_signature(raw_body: bytes, x_bold_signature: str | None) -> None:
    secret = os.environ.get("BOLD_WEBHOOK_SECRET_KEY", os.environ.get("BOLD_SECRET_KEY"))
    if secret is None:
        return

    if not x_bold_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma Bold requerida")

    encoded_body = base64.b64encode(raw_body)
    expected = hmac.new(secret.encode("utf-8"), encoded_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_bold_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma Bold invalida")


def _validate_webhook_token(x_bold_token: str | None) -> None:
    expected = os.getenv("BOLD_WEBHOOK_TOKEN", "change-me-super-secret")
    if x_bold_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de webhook invalido")


def _validate_webhook_auth(raw_body: bytes, x_bold_signature: str | None, x_bold_token: str | None) -> None:
    if "BOLD_WEBHOOK_SECRET_KEY" in os.environ or "BOLD_SECRET_KEY" in os.environ:
        _validate_webhook_signature(raw_body, x_bold_signature)
        return
    _validate_webhook_token(x_bold_token)


def _order_query(db: Session):
    return (
        db.query(Pedido)
        .options(
            joinedload(Pedido.usuario),
            joinedload(Pedido.estado),
            joinedload(Pedido.pago),
            joinedload(Pedido.detalles)
            .joinedload(DetallePedido.variante)
            .joinedload(VarianteProducto.producto),
        )
    )


def _serialize_order(order: Pedido) -> OrderResponse:
    user = order.usuario
    client = " ".join(
        part for part in [
            getattr(user, "nombre_usuario", ""),
            getattr(user, "apellido_usuario", ""),
        ] if part
    ).strip() or "Sin cliente"
    return OrderResponse(
        id_pedido=order.id_pedido,
        cliente=client,
        total=order.total,
        id_estado_pedido=order.id_estado_pedido,
        estado=order.estado.descripcion_estado if order.estado else "Sin estado",
        pago_status="PAGADO" if order.pago else "PENDIENTE",
        detalles=[
            OrderDetailResponse(
                sku=detail.variante.sku,
                producto=detail.variante.producto.nombre_producto,
                cantidad=detail.cantidad,
                precio_unitario=detail.precio_unitario,
            )
            for detail in order.detalles
        ],
    )


@router.get("/pedidos", response_model=list[OrderResponse])
def list_pedidos(db: Session = Depends(get_db)):
    try:
        orders = _order_query(db).order_by(Pedido.id_pedido.desc()).limit(100).all()
        return [_serialize_order(order) for order in orders]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudieron cargar pedidos: {exc}") from exc


@router.get("/pedidos/{id_pedido}", response_model=OrderResponse)
def get_pedido(id_pedido: int, db: Session = Depends(get_db)):
    try:
        order = _order_query(db).filter(Pedido.id_pedido == id_pedido).one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return _serialize_order(order)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo cargar pedido: {exc}") from exc


@router.post("/checkout/orders", response_model=CreateCheckoutOrderResponse)
def create_checkout_order(payload: CreateCheckoutOrderPayload, db: Session = Depends(get_db)):
    try:
        order = create_order_with_stock_reservation(db, payload.model_dump())
        return CreateCheckoutOrderResponse(
            ok=True,
            order_id=order.id_pedido,
            total=order.total,
            message="Pedido pendiente creado y stock reservado temporalmente",
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"No se pudo crear la reserva del pedido: {exc}") from exc


@router.post("/reservations/expire", response_model=ExpireReservationsResponse)
def expire_reservations(payload: ExpireReservationsPayload, db: Session = Depends(get_db)):
    try:
        expired = expire_pending_reservations(db, payload.minutes)
        return ExpireReservationsResponse(
            ok=True,
            expired_order_ids=expired,
            message=f"{len(expired)} reservas expiradas y devueltas al inventario",
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"No se pudieron expirar reservas: {exc}") from exc


@router.post("/webhook/bold", response_model=WebhookResponse)
async def bold_webhook(
    payload: BoldWebhookPayload,
    request: Request,
    x_bold_token: str | None = Header(default=None, alias="X-Bold-Token"),
    x_bold_signature: str | None = Header(default=None, alias="x-bold-signature"),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    _validate_webhook_auth(raw_body, x_bold_signature, x_bold_token)
    raw_payload = await request.json()

    try:
        result = process_bold_payment(db, payload.model_dump(), raw_payload)
        return WebhookResponse(**result)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        detail = getattr(getattr(exc, "orig", None), "diag", None)
        constraint = getattr(detail, "constraint_name", None) if detail else None
        raise HTTPException(status_code=409, detail=f"Conflicto de integridad en Bold: {constraint or exc.orig}") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando webhook Bold: {exc}") from exc

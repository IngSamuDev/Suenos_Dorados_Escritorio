from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.schemas import DescuentoCreate, DescuentoResponse, DescuentoUpdate, ProductoConDescuentoResponse
from controllers.descuentos_controller import DiscountController
from database import get_db

router = APIRouter(tags=["descuentos"])


@router.get("/descuentos", response_model=list[DescuentoResponse])
def list_discounts(db: Session = Depends(get_db)):
    return DiscountController(db).list_discounts()


@router.post("/descuentos", response_model=DescuentoResponse, status_code=status.HTTP_201_CREATED)
def create_discount(payload: DescuentoCreate, db: Session = Depends(get_db)):
    try:
        return DiscountController(db).create_discount(payload.model_dump())
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear el descuento. Revisa codigo unico, producto y fechas.") from exc


@router.put("/descuentos/{discount_id}", response_model=DescuentoResponse)
def update_discount(discount_id: int, payload: DescuentoUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar")
    try:
        return DiscountController(db).update_discount(discount_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo actualizar el descuento. Revisa codigo unico, producto y fechas.") from exc


@router.delete("/descuentos/{discount_id}", response_model=DescuentoResponse)
def delete_discount(discount_id: int, db: Session = Depends(get_db)):
    try:
        return DiscountController(db).delete_discount(discount_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/productos/{product_id}/precio-descuento", response_model=ProductoConDescuentoResponse)
def get_product_discount_price(product_id: int, db: Session = Depends(get_db)):
    try:
        return DiscountController(db).product_with_discount_prices(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc



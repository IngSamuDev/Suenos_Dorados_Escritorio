from fastapi import APIRouter

from api.crud import register_crud_routes
from models.ventas_model import Direccion, Envio, EstadoEnvio

router = APIRouter(prefix="/api/admin/logistics", tags=["logistics"])

register_crud_routes(router, "/shipments", Envio, "id_envio")
register_crud_routes(router, "/shipping-statuses", EstadoEnvio, "id_estado_envio")
register_crud_routes(router, "/addresses", Direccion, "id_direccion")



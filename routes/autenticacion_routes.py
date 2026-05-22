from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from api.crud import register_crud_routes
from api.serialization import model_to_dict
from controllers.autenticacion_controller import AuthController
from database import get_db
from models.ventas_model import Direccion
from models.usuarios_model import Rol, Usuario

router = APIRouter(prefix="/api/admin/auth", tags=["auth"])


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    usuario = AuthController(db).login(data.get("correo_electronico"), data.get("password"))
    return model_to_dict(usuario)


@router.post("/init-admin")
def init_admin(db: Session = Depends(get_db)):
    usuario = AuthController(db).init_admin()
    return model_to_dict(usuario)


register_crud_routes(router, "/users", Usuario, "id_usuario")
register_crud_routes(router, "/roles", Rol, "id_rol")
register_crud_routes(router, "/addresses", Direccion, "id_direccion")



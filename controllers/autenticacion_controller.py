from sqlalchemy.orm import Session

from models.usuarios_model import Rol, Usuario
from utils.security import hash_password, verify_password


class AuthController:
    def __init__(self, db: Session):
        self.db = db

    def init_admin(self):
        admin_rol = self.db.query(Rol).filter_by(descripcion_rol="Administrador").first()
        if not admin_rol:
            admin_rol = Rol(descripcion_rol="Administrador")
            self.db.add(admin_rol)
            self.db.commit()
            self.db.refresh(admin_rol)

        admin_exists = self.db.query(Usuario).filter_by(correo_electronico="admin@gmail.com").first()
        if admin_exists:
            return admin_exists

        admin = Usuario(
            id_rol=admin_rol.id_rol,
            nombre_usuario="Admin",
            apellido_usuario="Maestro",
            correo_electronico="admin@gmail.com",
            contrasena_hash=hash_password("admin1234"),
            estado=True,
        )
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def login(self, correo: str, password: str):
        usuario = self.db.query(Usuario).filter_by(correo_electronico=correo, estado=True).first()
        if usuario and verify_password(password, usuario.contrasena_hash):
            return usuario
        return None



from controllers.crud_base_controller import BaseCrudController


class UsuariosController(BaseCrudController):
    """Controlador del CRUD administrativo de usuarios."""

    group_id = "usuarios"

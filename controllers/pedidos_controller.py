from controllers.crud_base_controller import BaseCrudController
from controllers.ventas_controller import SalesController


class PedidosController(BaseCrudController):
    """Controlador del CRUD administrativo de pedidos."""

    group_id = "pedidos"


__all__ = ["PedidosController", "SalesController"]

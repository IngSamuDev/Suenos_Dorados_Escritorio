from controllers.crud_base_controller import BaseCrudController


class ProductosAdminController(BaseCrudController):
    """Controlador del CRUD administrativo de productos."""

    group_id = "productos"


class CatalogoController(BaseCrudController):
    """Controlador del CRUD administrativo de catálogo."""

    group_id = "catalogo"


class MedidasController(BaseCrudController):
    """Controlador del CRUD administrativo de medidas."""

    group_id = "medidas"


class ColoresController(BaseCrudController):
    """Controlador del CRUD administrativo de colores."""

    group_id = "colores"


class ImagenesController(BaseCrudController):
    """Controlador del CRUD administrativo de imágenes."""

    group_id = "imagenes"


class ColeccionesController(BaseCrudController):
    """Controlador del CRUD administrativo de colecciones."""

    group_id = "colecciones"


class InventarioAdminController(BaseCrudController):
    """Controlador del CRUD administrativo de inventario."""

    group_id = "inventario"

from fastapi import APIRouter

from api.crud import register_crud_routes
from models.catalogo_model import Categoria, Coleccion, Color, ImagenProducto, Medida, Producto, VarianteProducto

router = APIRouter(prefix="/api/admin/catalog", tags=["catalog"])

register_crud_routes(router, "/categories", Categoria, "id_categoria")
register_crud_routes(router, "/collections", Coleccion, "id_coleccion")
register_crud_routes(router, "/colors", Color, "id_color")
register_crud_routes(router, "/measures", Medida, "id_medida")
register_crud_routes(router, "/products", Producto, "id_producto")
register_crud_routes(router, "/variants", VarianteProducto, "id_variante")
register_crud_routes(router, "/product-images", ImagenProducto, "id_imagen")



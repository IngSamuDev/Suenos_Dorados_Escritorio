from controllers.productos_controller import CatalogoController
from views.crud_base_view import BaseCrudView
from views.descuentos_view import DescuentosCrudMixin
from views.productos_view import InventarioCrudMixin, PRODUCTOS_DISPLAY_QUERIES


CATALOGO_GROUP = {'title': 'Catálogo',
 'tables': [{'label': 'Productos',
             'table': 'productos',
             'pk': 'id_producto',
             'fields': [('id_categoria', 'int'),
                        ('id_coleccion', 'int'),
                        ('nombre_producto', 'str'),
                        ('descripcion_producto', 'str'),
                        ('slug', 'str'),
                        ('estado_producto', 'bool')]},
            {'label': 'Descuentos',
             'table': 'descuentos',
             'pk': 'id',
             'fields': [('id_producto', 'int'),
                        ('codigo', 'str'),
                        ('porcentaje_descuento', 'decimal'),
                        ('fecha_inicio', 'date'),
                        ('fecha_fin', 'date'),
                        ('is_active', 'bool')]},
            {'label': 'Variantes SKU',
             'table': 'variantes_producto',
             'pk': 'id_variante',
             'fields': [('id_producto', 'int'),
                        ('id_medida', 'int'),
                        ('id_color', 'int'),
                        ('sku', 'str'),
                        ('precio', 'decimal'),
                        ('referencia', 'str'),
                        ('stock', 'int'),
                        ('estado', 'bool')]},
            {'label': 'Categorías',
             'table': 'categorias',
             'pk': 'id_categoria',
             'fields': [('nombre_categoria', 'str'), ('descripcion_categoria', 'str'), ('slug', 'str')]},
            {'label': 'Colecciones',
             'table': 'colecciones',
             'pk': 'id_coleccion',
             'fields': [('id_categoria', 'int'),
                        ('nombre_coleccion', 'str'),
                        ('descripcion_coleccion', 'str'),
                        ('estado', 'bool')]},
            {'label': 'Colores',
             'table': 'colores',
             'pk': 'id_color',
             'fields': [('nombre_color', 'str'), ('codigo_hex', 'str')]},
            {'label': 'Medidas',
             'table': 'medidas',
             'pk': 'id_medida',
             'fields': [('nombre_medida', 'str'),
                        ('ancho_cm', 'decimal'),
                        ('largo_cm', 'decimal'),
                        ('descripcion', 'str')]},
            {'label': 'Imágenes',
             'table': 'imagenes_producto',
             'pk': 'id_imagen',
             'fields': [('id_producto', 'int'),
                        ('id_color', 'int'),
                        ('url_imagen', 'str'),
                        ('orden', 'int'),
                        ('es_principal', 'bool')]}]}


class CatalogoView(DescuentosCrudMixin, InventarioCrudMixin, BaseCrudView):
    def __init__(self):
        self.controller = CatalogoController()
        super().__init__(self.controller.group_id, CATALOGO_GROUP, PRODUCTOS_DISPLAY_QUERIES)


__all__ = ["CatalogoView"]

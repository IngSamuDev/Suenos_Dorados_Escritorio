LOOKUP_CONFIG = {'id_rol': {'table': 'roles', 'pk': 'id_rol', 'columns': ['descripcion_rol']},
 'id_categoria': {'table': 'categorias', 'pk': 'id_categoria', 'columns': ['nombre_categoria', 'slug']},
 'id_coleccion': {'table': 'colecciones', 'pk': 'id_coleccion', 'columns': ['nombre_coleccion']},
 'id_producto': {'table': 'productos', 'pk': 'id_producto', 'columns': ['nombre_producto', 'slug']},
 'id_medida': {'table': 'medidas', 'pk': 'id_medida', 'columns': ['nombre_medida', 'descripcion']},
 'id_color': {'table': 'colores', 'pk': 'id_color', 'columns': ['nombre_color', 'codigo_hex']},
 'id_usuario': {'table': 'usuarios',
                'pk': 'id_usuario',
                'columns': ['nombre_usuario', 'apellido_usuario', 'correo_electronico']},
 'id_direccion': {'table': 'direcciones',
                  'pk': 'id_direccion',
                  'columns': ['descripcion_direccion', 'descripcion_municipio']},
 'id_estado_pedido': {'table': 'estado_pedido', 'pk': 'id_estado_pedido', 'columns': ['descripcion_estado']},
 'id_estado_envio': {'table': 'estado_envio', 'pk': 'id_estado_envio', 'columns': ['descripcion_estado']},
 'id_pedido': {'table': 'pedidos',
               'pk': 'id_pedido',
               'columns': ['id_pedido', 'nombre_usuario', 'apellido_usuario'],
               'select': """
                   SELECT p.id_pedido, u.nombre_usuario, u.apellido_usuario
                   FROM pedidos p
                   LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario
                   ORDER BY p.id_pedido DESC
               """},
 'id_variante': {'table': 'variantes_producto', 'pk': 'id_variante', 'columns': ['sku', 'referencia']},
 'id_respuesta_bold': {'table': 'respuesta_bold', 'pk': 'id_respuesta', 'columns': ['transaction_id', 'status']}}

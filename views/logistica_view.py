from sqlalchemy import text

from controllers.logistica_controller import LogisticaController
from database import SessionLocal
from utils.theme import Tema
from views.crud_base_view import BaseCrudView


LOGISTICA_GROUP = {'title': 'Logística y envíos',
 'tables': [{'label': 'Envíos',
             'table': 'envio',
             'pk': 'id_envio',
             'fields': [('id_pedido', 'int'),
                        ('id_estado_envio', 'int'),
                        ('numero_guia', 'str'),
                        ('transportadora', 'str'),
                        ('fecha_envio', 'str'),
                        ('fecha_entrega_estimada', 'str'),
                        ('fecha_entrega_real', 'str')]},
            {'label': 'Estados envío',
             'table': 'estado_envio',
             'pk': 'id_estado_envio',
             'fields': [('descripcion_estado', 'str')]},
            {'label': 'Direcciones',
             'table': 'direcciones',
             'pk': 'id_direccion',
             'fields': [('id_usuario', 'int'),
                        ('descripcion_direccion', 'str'),
                        ('descripcion_barrio', 'str'),
                        ('descripcion_municipio', 'str'),
                        ('descripcion_departamento', 'str'),
                        ('es_principal', 'bool')]}]}
LOGISTICA_DISPLAY_QUERIES = {'envio': {'columns': ['pedido',
                       'estado',
                       'numero_guia',
                       'transportadora',
                       'fecha_envio',
                       'fecha_entrega_estimada',
                       'fecha_entrega_real'],
           'headings': ['Pedido', 'Estado', 'Guía', 'Transportadora', 'Envío', 'Entrega estimada', 'Entrega real'],
           'select': '\n'
                     '            SELECT e.id_envio, e.id_pedido, e.id_estado_envio, e.numero_guia, e.transportadora,\n'
                     '                   e.fecha_envio, e.fecha_entrega_estimada, e.fecha_entrega_real,\n'
                     "                   CONCAT('Pedido ', e.id_pedido) AS pedido,\n"
                     '                   ee.descripcion_estado AS estado\n'
                     '            FROM envio e\n'
                     '            LEFT JOIN estado_envio ee ON ee.id_estado_envio = e.id_estado_envio\n'
                     '        ',
           'search': ['CAST(e.id_pedido AS TEXT)',
                      'ee.descripcion_estado',
                      'e.numero_guia',
                      'e.transportadora',
                      'CAST(e.fecha_envio AS TEXT)',
                      'CAST(e.fecha_entrega_estimada AS TEXT)',
                      'CAST(e.fecha_entrega_real AS TEXT)'],
           'order': 'e.id_envio'},
 'estado_envio': {'columns': ['descripcion_estado'],
                  'headings': ['Estado de envío'],
                  'select': 'SELECT id_estado_envio, descripcion_estado FROM estado_envio',
                  'search': ['descripcion_estado'],
                  'order': 'id_estado_envio'}}


class LogisticaView(BaseCrudView):
    def __init__(self):
        self.controller = LogisticaController()
        super().__init__(self.controller.group_id, LOGISTICA_GROUP, LOGISTICA_DISPLAY_QUERIES)

    def _set_state(self, kind, description):
        if self.selected_record_id is None:
            self._snack("Selecciona un registro primero", Tema.WARNING)
            return
        table = "estado_pedido" if kind == "pedido" else "estado_envio"
        id_field = "id_estado_pedido" if kind == "pedido" else "id_estado_envio"
        pk = "id_estado_pedido" if kind == "pedido" else "id_estado_envio"
        target = "pedidos" if kind == "pedido" else "envio"
        if kind == "pedido" and description in ("Pagado", "Despachado"):
            try:
                db = SessionLocal()
                try:
                    SalesController(db).approve_payment(self.selected_record_id, estado_destino=description)
                finally:
                    db.close()
                self._build_crud_content()
                if description == "Despachado":
                    self._snack("Pedido despachado, stock verificado y Kardex actualizado", Tema.SUCCESS)
                else:
                    self._snack("Pago aprobado, stock descontado y factura generada", Tema.SUCCESS)
            except Exception as exc:
                self._snack(f"Error al actualizar pedido: {exc}", Tema.ERROR)
            return
        try:
            db = SessionLocal()
            try:
                state_id = db.execute(text(f"SELECT {pk} FROM {table} WHERE descripcion_estado = :d"), {"d": description}).scalar()
                if not state_id:
                    raise ValueError(f"No existe el estado {description}")
                db.execute(text(f"UPDATE {target} SET {id_field} = :state_id WHERE {self.current_config['pk']} = :id"), {"state_id": state_id, "id": self.selected_record_id})
                db.commit()
            finally:
                db.close()
            self._build_crud_content()
            self._snack("Estado actualizado", Tema.SUCCESS)
        except Exception as exc:
            self._snack(f"Error al cambiar estado: {exc}", Tema.ERROR)

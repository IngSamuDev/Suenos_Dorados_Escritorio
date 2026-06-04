import flet as ft
from sqlalchemy import text

from controllers.descuentos_controller import DescuentosController
from database import SessionLocal
from utils.theme import Tema
from views.crud_base_view import BaseCrudView


DESCUENTOS_GROUP = {'title': 'Descuentos',
 'tables': [{'label': 'Descuentos',
             'table': 'descuentos',
             'pk': 'id',
             'fields': [('id_producto', 'int'),
                        ('codigo', 'str'),
                        ('porcentaje_descuento', 'decimal'),
                        ('fecha_inicio', 'date'),
                        ('fecha_fin', 'date'),
                        ('is_active', 'bool')]}]}
DESCUENTOS_DISPLAY_QUERIES = {'descuentos': {'columns': ['codigo', 'producto', 'porcentaje_descuento', 'fecha_inicio', 'fecha_fin', 'estado_texto'],
                'headings': ['Código', 'Producto', '%', 'Inicio', 'Fin', 'Estado'],
                'select': '\n'
                          '            SELECT d.id, d.id_producto, d.codigo, d.porcentaje_descuento, d.fecha_inicio, '
                          'd.fecha_fin, d.is_active,\n'
                          "                   COALESCE(p.nombre_producto, 'Global') AS producto,\n"
                          "                   CASE WHEN d.is_active THEN 'Activo' ELSE 'Inactivo' END AS estado_texto\n"
                          '            FROM descuentos d\n'
                          '            LEFT JOIN productos p ON p.id_producto = d.id_producto\n'
                          '        ',
                'search': ['d.codigo',
                           'p.nombre_producto',
                           'CAST(d.porcentaje_descuento AS TEXT)',
                           'CAST(d.fecha_inicio AS TEXT)',
                           'CAST(d.fecha_fin AS TEXT)'],
                'order': 'd.id'}}


class DescuentosCrudMixin:
    def _deactivate_expired_discounts(self):
        try:
            db = SessionLocal()
            try:
                db.execute(text("""
                    UPDATE descuentos
                    SET is_active = FALSE
                    WHERE is_active = TRUE
                      AND fecha_fin < CURRENT_DATE
                """))
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

    def _load_discounts_table(self, config):
        self._deactivate_expired_discounts()
        spec = self.display_queries["descuentos"]
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = " WHERE " + " OR ".join(f"{col} ILIKE :search" for col in spec["search"])
            params["search"] = f"%{search_value}%"
        sql = f"{spec['select']} {where_sql} ORDER BY {spec['order']} DESC LIMIT 35"
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar descuentos", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        rows = []
        for item in rows_data:
            record = dict(item)
            rows.append(
                ft.DataRow(
                    cells=[
                        self._action_cell(record),
                        self._text_cell(record.get("codigo")),
                        self._text_cell(record.get("producto")),
                        self._text_cell(record.get("porcentaje_descuento")),
                        self._text_cell(record.get("fecha_inicio")),
                        self._text_cell(record.get("fecha_fin")),
                        self._status_cell(record.get("estado_texto")),
                    ]
                )
            )
        return self._table_panel(f"{len(rows_data)} descuentos", ["Acciones", "Código", "Producto", "%", "Inicio", "Fin", "Estado"], rows)



class DescuentosView(DescuentosCrudMixin, BaseCrudView):
    def __init__(self):
        self.controller = DescuentosController()
        super().__init__(self.controller.group_id, DESCUENTOS_GROUP, DESCUENTOS_DISPLAY_QUERIES)

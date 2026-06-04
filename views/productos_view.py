from datetime import datetime
import re

import flet as ft
from sqlalchemy import text

from config import BASE_DIR
from controllers.productos_controller import (
    ColeccionesController,
    ColoresController,
    ImagenesController,
    InventarioAdminController,
    MedidasController,
    ProductosAdminController,
)
from database import SessionLocal
from utils.excel_generator import export_inventory_to_excel
from utils.theme import Tema
from views.crud_base_view import BaseCrudView


PRODUCTOS_GROUPS = {'productos': {'title': 'Productos',
               'tables': [{'label': 'Productos',
                           'table': 'productos',
                           'pk': 'id_producto',
                           'fields': [('id_categoria', 'int'),
                                      ('id_coleccion', 'int'),
                                      ('nombre_producto', 'str'),
                                      ('descripcion_producto', 'str'),
                                      ('slug', 'str'),
                                      ('estado_producto', 'bool')]}]},
 'medidas': {'title': 'Medidas',
             'tables': [{'label': 'Medidas',
                         'table': 'medidas',
                         'pk': 'id_medida',
                         'fields': [('nombre_medida', 'str'),
                                    ('ancho_cm', 'decimal'),
                                    ('largo_cm', 'decimal'),
                                    ('descripcion', 'str')]}]},
 'colores': {'title': 'Colores',
             'tables': [{'label': 'Colores',
                         'table': 'colores',
                         'pk': 'id_color',
                         'fields': [('nombre_color', 'str'), ('codigo_hex', 'str')]}]},
 'imagenes': {'title': 'Imágenes',
              'tables': [{'label': 'Imágenes',
                          'table': 'imagenes_producto',
                          'pk': 'id_imagen',
                          'fields': [('id_producto', 'int'),
                                     ('id_color', 'int'),
                                     ('url_imagen', 'str'),
                                     ('orden', 'int'),
                                     ('es_principal', 'bool')]}]},
 'colecciones': {'title': 'Colecciones',
                 'tables': [{'label': 'Colecciones',
                             'table': 'colecciones',
                             'pk': 'id_coleccion',
                             'fields': [('id_categoria', 'int'),
                                        ('nombre_coleccion', 'str'),
                                        ('descripcion_coleccion', 'str'),
                                        ('estado', 'bool')]},
                            {'label': 'Categorías',
                             'table': 'categorias',
                             'pk': 'id_categoria',
                             'fields': [('nombre_categoria', 'str'),
                                        ('descripcion_categoria', 'str'),
                                        ('slug', 'str')]},
                            {'label': 'Productos por colección',
                             'table': 'productos',
                             'pk': 'id_producto',
                             'fields': [('id_categoria', 'int'),
                                        ('id_coleccion', 'int'),
                                        ('nombre_producto', 'str'),
                                        ('descripcion_producto', 'str'),
                                        ('slug', 'str'),
                                        ('estado_producto', 'bool')]}]},
 'inventario': {'title': 'Inventario',
                'tables': [{'label': 'Stock por SKU',
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
                           {'label': 'Movimientos Kardex',
                            'table': 'movimientos_inventario',
                            'pk': 'id_movimiento',
                            'fields': [('id_variante', 'int'),
                                       ('tipo_movimiento', 'str'),
                                       ('cantidad', 'int'),
                                       ('stock_anterior', 'int'),
                                       ('stock_nuevo', 'int'),
                                       ('referencia_documento', 'str'),
                                       ('observacion', 'str')]}]}}
PRODUCTOS_DISPLAY_QUERIES = {'productos': {'columns': ['nombre_producto', 'categoria', 'coleccion', 'slug', 'estado_texto'],
               'headings': ['Producto', 'Categoría', 'Colección', 'Slug', 'Estado'],
               'select': '\n'
                         '            SELECT p.id_producto, p.id_categoria, p.id_coleccion, p.nombre_producto, '
                         'p.descripcion_producto,\n'
                         '                   p.slug, p.estado_producto, p.fecha_creacion,\n'
                         '                   ca.nombre_categoria AS categoria,\n'
                         '                   co.nombre_coleccion AS coleccion,\n'
                         "                   CASE WHEN p.estado_producto THEN 'Activo' ELSE 'Inactivo' END AS "
                         'estado_texto\n'
                         '            FROM productos p\n'
                         '            LEFT JOIN categorias ca ON ca.id_categoria = p.id_categoria\n'
                         '            LEFT JOIN colecciones co ON co.id_coleccion = p.id_coleccion\n'
                         '        ',
               'search': ['p.nombre_producto',
                          'p.descripcion_producto',
                          'p.slug',
                          'ca.nombre_categoria',
                          'co.nombre_coleccion'],
               'order': 'p.id_producto'},
 'categorias': {'columns': ['nombre_categoria', 'descripcion_categoria', 'slug'],
                'headings': ['Categoría', 'Descripción', 'Slug'],
                'select': 'SELECT id_categoria, nombre_categoria, descripcion_categoria, slug FROM categorias',
                'search': ['nombre_categoria', 'descripcion_categoria', 'slug'],
                'order': 'id_categoria'},
 'colecciones': {'columns': ['nombre_coleccion', 'categoria', 'descripcion_coleccion', 'estado_texto'],
                 'headings': ['Colección', 'Categoría', 'Descripción', 'Estado'],
                 'select': '\n'
                           '            SELECT co.id_coleccion, co.id_categoria, co.nombre_coleccion, '
                           'co.descripcion_coleccion, co.estado,\n'
                           '                   ca.nombre_categoria AS categoria,\n'
                           "                   CASE WHEN co.estado THEN 'Activo' ELSE 'Inactivo' END AS estado_texto\n"
                           '            FROM colecciones co\n'
                           '            LEFT JOIN categorias ca ON ca.id_categoria = co.id_categoria\n'
                           '        ',
                 'search': ['co.nombre_coleccion', 'co.descripcion_coleccion', 'ca.nombre_categoria'],
                 'order': 'co.id_coleccion'},
 'colores': {'columns': ['nombre_color', 'codigo_hex'],
             'headings': ['Color', 'Código'],
             'select': 'SELECT id_color, nombre_color, codigo_hex FROM colores',
             'search': ['nombre_color', 'codigo_hex'],
             'order': 'id_color'},
 'medidas': {'columns': ['nombre_medida', 'ancho_cm', 'largo_cm', 'descripcion'],
             'headings': ['Medida', 'Ancho cm', 'Largo cm', 'Descripción'],
             'select': 'SELECT id_medida, nombre_medida, ancho_cm, largo_cm, descripcion FROM medidas',
             'search': ['nombre_medida', 'descripcion', 'CAST(ancho_cm AS TEXT)', 'CAST(largo_cm AS TEXT)'],
             'order': 'id_medida'},
 'imagenes_producto': {'columns': ['producto', 'color', 'url_imagen', 'orden', 'estado_texto'],
                       'headings': ['Producto', 'Color', 'Imagen', 'Orden', 'Estado'],
                       'select': '\n'
                                 '            SELECT i.id_imagen, i.id_producto, i.id_color, i.url_imagen, i.orden, '
                                 'i.es_principal,\n'
                                 '                   p.nombre_producto AS producto,\n'
                                 '                   c.nombre_color AS color,\n'
                                 "                   CASE WHEN i.es_principal THEN 'Activo' ELSE 'Inactivo' END AS "
                                 'estado_texto\n'
                                 '            FROM imagenes_producto i\n'
                                 '            LEFT JOIN productos p ON p.id_producto = i.id_producto\n'
                                 '            LEFT JOIN colores c ON c.id_color = i.id_color\n'
                                 '        ',
                       'search': ['p.nombre_producto', 'c.nombre_color', 'i.url_imagen', 'CAST(i.orden AS TEXT)'],
                       'order': 'i.id_imagen'},
 'movimientos_inventario': {'columns': ['producto',
                                        'sku',
                                        'tipo_movimiento',
                                        'cantidad',
                                        'stock_anterior',
                                        'stock_nuevo',
                                        'referencia_documento',
                                        'fecha_movimiento'],
                            'headings': ['Producto',
                                         'SKU',
                                         'Movimiento',
                                         'Cantidad',
                                         'Stock anterior',
                                         'Stock nuevo',
                                         'Referencia',
                                         'Fecha'],
                            'select': '\n'
                                      '            SELECT mi.id_movimiento, mi.id_variante, mi.tipo_movimiento, '
                                      'mi.cantidad, mi.stock_anterior,\n'
                                      '                   mi.stock_nuevo, mi.referencia_documento, mi.observacion, '
                                      'mi.fecha_movimiento,\n'
                                      '                   p.nombre_producto AS producto,\n'
                                      '                   v.sku AS sku\n'
                                      '            FROM movimientos_inventario mi\n'
                                      '            LEFT JOIN variantes_producto v ON v.id_variante = mi.id_variante\n'
                                      '            LEFT JOIN productos p ON p.id_producto = v.id_producto\n'
                                      '        ',
                            'search': ['p.nombre_producto',
                                       'v.sku',
                                       'mi.tipo_movimiento',
                                       'CAST(mi.cantidad AS TEXT)',
                                       'mi.referencia_documento',
                                       'mi.observacion',
                                       'CAST(mi.fecha_movimiento AS TEXT)'],
                            'order': 'mi.id_movimiento'}}


class ProductosView(BaseCrudView):
    def __init__(self):
        self.controller = ProductosAdminController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["productos"], PRODUCTOS_DISPLAY_QUERIES)


class MedidasView(BaseCrudView):
    def __init__(self):
        self.controller = MedidasController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["medidas"], PRODUCTOS_DISPLAY_QUERIES)


class ColoresView(BaseCrudView):
    def __init__(self):
        self.controller = ColoresController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["colores"], PRODUCTOS_DISPLAY_QUERIES)


class ImagenesView(BaseCrudView):
    def __init__(self):
        self.controller = ImagenesController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["imagenes"], PRODUCTOS_DISPLAY_QUERIES)


class ColeccionesView(BaseCrudView):
    def __init__(self):
        self.controller = ColeccionesController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["colecciones"], PRODUCTOS_DISPLAY_QUERIES)


class InventarioCrudMixin:
    def _stock_adjust_panel(self):
        return ft.Container(
            bgcolor=Tema.GOLD_SOFT,
            border_radius=14,
            padding=18,
            border=ft.Border(
                left=ft.BorderSide(4, Tema.GOLD),
                right=ft.BorderSide(1, "#F4D58A"),
                top=ft.BorderSide(1, "#F4D58A"),
                bottom=ft.BorderSide(1, "#F4D58A"),
            ),
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.07, "#172033"), offset=ft.Offset(0, 8)),
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(spacing=3, controls=[
                                ft.Text("Ajuste rápido de stock", size=15, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                                ft.Text("Selecciona un SKU, escribe unidades y aplica entrada o salida de inventario.", size=12, color=Tema.TEXT_MUTED),
                            ]),
                            ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, color="#B35A00", size=26),
                        ],
                    ),
                    ft.Row(
                        spacing=12,
                        wrap=True,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self._build_stock_variant_selector(),
                            self._build_stock_delta_field(),
                            self._stock_button("Agregar stock", ft.Icons.ADD_ROUNDED, 1),
                            self._stock_button("Disminuir stock", ft.Icons.REMOVE_ROUNDED, -1),
                        ],
                    ),
                ],
            ),
        )

    def _build_stock_variant_selector(self):
        self.stock_variant_selector = ft.Dropdown(
            label="SKU",
            width=320,
            dense=True,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=220,
            menu_width=420,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            options=self._stock_variant_options(),
            hint_text="Busca producto o SKU",
        )
        if self.selected_record_id is not None:
            self.stock_variant_selector.value = str(self.selected_record_id)
        return self.stock_variant_selector

    def _stock_variant_options(self):
        options = [ft.dropdown.Option(key="", text="Selecciona SKU")]
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text("""
                    SELECT v.id_variante, v.sku, v.referencia, v.stock, p.nombre_producto
                    FROM variantes_producto v
                    LEFT JOIN productos p ON p.id_producto = v.id_producto
                    ORDER BY v.id_variante DESC
                    LIMIT 60
                """)).mappings().all()
            finally:
                db.close()
        except Exception:
            return options
        for row in rows:
            options.append(ft.dropdown.Option(key=str(row["id_variante"]), text=f"{row['nombre_producto'] or 'Producto'} | {row['sku']} | Stock {row['stock']}"))
        return options

    def _build_stock_delta_field(self):
        self.stock_delta_field = ft.TextField(
            label="Unidades",
            hint_text="Ej: 5",
            width=132,
            dense=True,
            prefix_icon=ft.Icons.NUMBERS_ROUNDED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=lambda _: self._adjust_stock(1),
        )
        return self.stock_delta_field

    def _stock_button(self, text_value, icon, sign):
        return ft.FilledButton(
            text_value,
            icon=icon,
            on_click=lambda _, stock_sign=sign: self._adjust_stock(stock_sign),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: "#B77900" if sign > 0 else "#6B7280", ft.ControlState.HOVERED: "#9A6700" if sign > 0 else "#4B5563"},
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(18, 13, 18, 13),
            ),
        )

    def _load_variants_stock_table(self, config):
        self.row_stock_fields = {}
        self.inventory_stock_rows = {}
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = """
                WHERE v.sku ILIKE :search
                   OR v.referencia ILIKE :search
                   OR p.nombre_producto ILIKE :search
                   OR m.nombre_medida ILIKE :search
                   OR c.nombre_color ILIKE :search
                   OR CAST(v.precio AS TEXT) ILIKE :search
                   OR CAST(v.stock AS TEXT) ILIKE :search
            """
            params["search"] = f"%{search_value}%"
        sql = f"""
            SELECT
                v.id_variante, v.id_producto, v.id_medida, v.id_color, v.sku, v.precio, v.referencia, v.stock, v.estado,
                p.nombre_producto AS producto,
                m.nombre_medida AS medida,
                c.nombre_color AS color,
                CASE
                    WHEN v.stock <= 0 THEN 'Agotado'
                    WHEN v.stock <= 3 THEN 'Stock bajo'
                    ELSE 'Normal'
                END AS estado_stock,
                CASE WHEN v.estado THEN 'Activo' ELSE 'Inactivo' END AS estado_texto
            FROM variantes_producto v
            LEFT JOIN productos p ON p.id_producto = v.id_producto
            LEFT JOIN medidas m ON m.id_medida = v.id_medida
            LEFT JOIN colores c ON c.id_color = v.id_color
            {where_sql}
            ORDER BY v.id_variante DESC
            LIMIT 35
        """
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar inventario", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        rows = []
        for item in rows_data:
            record = dict(item)
            variant_id = int(record["id_variante"])
            row = ft.DataRow(
                selected=self.selected_record_id == variant_id,
                on_select_change=lambda event, rec=record, row_variant_id=variant_id: self._select_stock_record(rec, row_variant_id, event),
                cells=[
                    self._inventory_action_cell(record, variant_id),
                ]
                + [
                    self._text_cell(record.get("producto")),
                    self._text_cell(record.get("medida")),
                    self._text_cell(record.get("color")),
                    self._text_cell(record.get("sku")),
                    self._text_cell(record.get("precio")),
                    self._text_cell(record.get("referencia")),
                    self._text_cell(record.get("stock")),
                    self._status_cell(record.get("estado_stock")),
                    self._status_cell(record.get("estado_texto")),
                ]
            )
            self.inventory_stock_rows[variant_id] = row
            rows.append(row)
        headings = ["Acciones", "Producto", "Medida", "Color", "SKU", "Precio", "Referencia", "Stock", "Estado stock", "Estado"]
        return self._table_panel(f"{len(rows_data)} registros", headings, rows)

    def _row_stock_field(self, variant_id):
        field = ft.TextField(
            value="1",
            width=64,
            height=36,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.row_stock_fields[variant_id] = field
        return field

    def _inventory_action_cell(self, record, variant_id):
        actions = [
            ft.IconButton(
                icon=ft.Icons.EDIT_ROUNDED,
                icon_color=Tema.GOLD,
                tooltip="Editar datos del SKU",
                on_click=lambda _, rec=record: self._edit_record(rec),
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                icon_color=Tema.ERROR,
                tooltip="Eliminar SKU",
                on_click=lambda _, rec=record: self._confirm_delete(rec),
            ),
        ]
        if "estado" in record:
            actions.append(self._boolean_switch(record, "estado"))
        return ft.DataCell(
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=actions,
            )
        )

    def _row_stock_icon(self, icon, tooltip, variant_id, sign):
        return ft.IconButton(
            icon=icon,
            tooltip=tooltip,
            icon_color=ft.Colors.WHITE,
            bgcolor="#9A6700",
            width=36,
            height=36,
            on_click=lambda _, row_variant_id=variant_id, row_sign=sign: self._adjust_stock_for_variant(row_variant_id, row_sign),
        )

    def _select_stock_record(self, record, variant_id, event=None):
        self.selected_record_id = variant_id
        for row_variant_id, row in getattr(self, "inventory_stock_rows", {}).items():
            row.selected = row_variant_id == variant_id
        if self.stock_variant_selector:
            self.stock_variant_selector.value = str(variant_id)
        if self.stock_delta_field:
            self.stock_delta_field.value = "1"
        label = record.get("producto") or record.get("sku") or "SKU"
        self.selected_record_text.value = f"SKU seleccionado: {label} | Stock actual: {record.get('stock')}"
        try:
            if event and event.control:
                event.control.selected = True
            self.crud_area.update()
        except RuntimeError:
            pass

    def _export_inventory_excel(self):
        sql = """
            SELECT
                v.id_variante,
                p.nombre_producto AS producto,
                c.nombre_categoria AS categoria,
                m.nombre_medida AS medida,
                co.nombre_color AS color,
                v.sku,
                v.referencia,
                v.precio,
                v.stock,
                v.estado
            FROM variantes_producto v
            JOIN productos p ON p.id_producto = v.id_producto
            LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
            LEFT JOIN medidas m ON m.id_medida = v.id_medida
            LEFT JOIN colores co ON co.id_color = v.id_color
            ORDER BY v.stock ASC, v.sku ASC
        """
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text(sql)).mappings().all()
            finally:
                db.close()
            file_path = export_inventory_to_excel(rows, BASE_DIR / "reportes")
            self._show_message("Excel generado", f"Inventario exportado en:\n{file_path}", Tema.SUCCESS)
        except Exception as exc:
            self._show_message("No se pudo exportar", str(exc), Tema.ERROR)

    def _selected_variant_id(self, db):
        if self.stock_variant_selector and self.stock_variant_selector.value:
            self.selected_record_id = int(self.stock_variant_selector.value)
            self.selected_record_text.value = f"Registro seleccionado: id_variante #{self.selected_record_id}"
            return self.selected_record_id
        if self.selected_record_id is not None:
            return self.selected_record_id
        sku_control = self.form_controls.get("sku")
        sku = (sku_control.value or "").strip() if sku_control else ""
        if not sku:
            raise ValueError("Selecciona un SKU en el campo de stock o con el lápiz de la tabla")
        variant_id = db.execute(text("SELECT id_variante FROM variantes_producto WHERE sku = :sku"), {"sku": sku}).scalar()
        if not variant_id:
            raise ValueError(f"No existe el SKU {sku}")
        self.selected_record_id = variant_id
        self.selected_record_text.value = f"Registro seleccionado: id_variante #{variant_id}"
        return variant_id

    def _ensure_kardex_table(self, db):
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS movimientos_inventario (
                id_movimiento SERIAL PRIMARY KEY,
                id_variante INT NOT NULL REFERENCES variantes_producto(id_variante) ON UPDATE CASCADE ON DELETE RESTRICT,
                tipo_movimiento VARCHAR(20) NOT NULL,
                cantidad INT NOT NULL,
                stock_anterior INT NOT NULL,
                stock_nuevo INT NOT NULL,
                referencia_documento VARCHAR(100),
                observacion TEXT,
                fecha_movimiento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.execute(text("ALTER TABLE movimientos_inventario ALTER COLUMN fecha_movimiento SET DEFAULT CURRENT_TIMESTAMP"))

    def _kardex_columns(self, db):
        return set(db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'movimientos_inventario'
        """)).scalars().all())

    def _adjust_stock(self, sign):
        try:
            raw_qty = (self.stock_delta_field.value or "").strip()
            if not re.fullmatch(r"\d+", raw_qty):
                raise ValueError("Unidades debe ser un número entero positivo")
            qty = int(raw_qty)
            if qty <= 0:
                raise ValueError("La cantidad debe ser mayor a cero")
            db = SessionLocal()
            try:
                variant_id = self._selected_variant_id(db)
            finally:
                db.close()
            new_stock = self._apply_stock_movement(
                variant_id=variant_id,
                qty=qty,
                sign=sign,
                reference="ADMIN",
                observation="Ajuste manual desde formulario de inventario",
            )

            if "stock" in self.form_controls:
                self.form_controls["stock"].value = str(new_stock)
            self.stock_delta_field.value = ""
            self._build_crud_content()
            self._show_message("Stock actualizado", f"Movimiento Kardex guardado. Nuevo stock: {new_stock}", Tema.SUCCESS)
        except Exception as exc:
            self._show_message("Error en stock", str(exc), Tema.ERROR)

    def _adjust_stock_for_variant(self, variant_id, sign):
        field = self.row_stock_fields.get(variant_id)
        try:
            qty = int((field.value if field else "1") or "0")
            if qty <= 0:
                raise ValueError("La cantidad debe ser mayor a cero")
            new_stock = self._apply_stock_movement(
                variant_id=variant_id,
                qty=qty,
                sign=sign,
                reference="ADMIN",
                observation="Ajuste manual desde fila de inventario",
            )
            if self.selected_record_id == variant_id and "stock" in self.form_controls:
                self.form_controls["stock"].value = str(new_stock)
            self._build_crud_content()
            self._snack(f"Stock actualizado. Nuevo stock: {new_stock}", Tema.SUCCESS)
        except Exception as exc:
            self._show_message("Error en stock", str(exc), Tema.ERROR)

    def _apply_stock_movement(self, variant_id, qty, sign, reference, observation):
        db = SessionLocal()
        try:
            self._ensure_kardex_table(db)
            row = db.execute(
                text("SELECT stock FROM variantes_producto WHERE id_variante = :id FOR UPDATE"),
                {"id": variant_id},
            ).mappings().first()
            if not row:
                raise ValueError("SKU no encontrado")
            previous = int(row["stock"])
            new_stock = previous + (qty * sign)
            if new_stock < 0:
                raise ValueError("El stock no puede quedar negativo")
            movement_date = datetime.now().strftime("%d/%m/%Y %H:%M")
            movement_observation = (
                f"Se añadieron {qty} unidades el {movement_date}"
                if sign > 0
                else f"Se quitaron {qty} unidades el {movement_date}"
            )
            db.execute(text("UPDATE variantes_producto SET stock = :stock WHERE id_variante = :id"), {"stock": new_stock, "id": variant_id})
            columns = self._kardex_columns(db)
            insert_columns = ["id_variante", "tipo_movimiento", "cantidad"]
            insert_values = [":id", ":tipo", ":cantidad"]
            params = {
                "id": variant_id,
                "tipo": "ENTRADA" if sign > 0 else "SALIDA",
                "cantidad": qty,
            }
            if "stock_anterior" in columns:
                insert_columns.append("stock_anterior")
                insert_values.append(":anterior")
                params["anterior"] = previous
            if "stock_nuevo" in columns:
                insert_columns.append("stock_nuevo")
                insert_values.append(":nuevo")
                params["nuevo"] = new_stock
            if "referencia_documento" in columns:
                insert_columns.append("referencia_documento")
                insert_values.append(":ref")
                params["ref"] = reference
            if "observacion" in columns:
                insert_columns.append("observacion")
                insert_values.append(":obs")
                params["obs"] = movement_observation
            if "motivo" in columns:
                insert_columns.append("motivo")
                insert_values.append(":motivo")
                params["motivo"] = movement_observation
            if "fecha_movimiento" in columns:
                insert_columns.append("fecha_movimiento")
                insert_values.append("CURRENT_TIMESTAMP")
            db.execute(
                text(f"INSERT INTO movimientos_inventario ({', '.join(insert_columns)}) VALUES ({', '.join(insert_values)})"),
                params,
            )
            db.commit()
            return new_stock
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


class InventarioView(InventarioCrudMixin, BaseCrudView):
    def __init__(self):
        self.controller = InventarioAdminController()
        super().__init__(self.controller.group_id, PRODUCTOS_GROUPS["inventario"], PRODUCTOS_DISPLAY_QUERIES)

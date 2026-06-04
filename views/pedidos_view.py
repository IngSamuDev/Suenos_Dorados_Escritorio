from decimal import Decimal
import os

import flet as ft
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from controllers.pedidos_controller import PedidosController
from controllers.ventas_controller import SalesController
from database import SessionLocal
from models.catalogo_model import VarianteProducto
from models.ventas_model import DetallePedido, Pedido
from utils.pdf_generator import generate_invoice_pdf
from utils.theme import Tema
from views.crud_base_view import BaseCrudView


PEDIDOS_GROUP = {'title': 'Pedidos y pagos',
 'tables': [{'label': 'Pedidos',
             'table': 'pedidos',
             'pk': 'id_pedido',
             'fields': [('id_usuario', 'int'),
                        ('id_direccion', 'int'),
                        ('id_estado_pedido', 'int'),
                        ('subtotal', 'decimal'),
                        ('descuento', 'discount'),
                        ('costo_envio', 'decimal'),
                        ('total', 'decimal')]},
            {'label': 'Detalle pedido',
             'table': 'detalle_pedido',
             'pk': 'id_detalle_pedido',
             'fields': [('id_pedido', 'int'),
                        ('id_variante', 'int'),
                        ('cantidad', 'int'),
                        ('precio_unitario', 'decimal')]},
            {'label': 'Estados pedido',
             'table': 'estado_pedido',
             'pk': 'id_estado_pedido',
             'fields': [('descripcion_estado', 'str')]},
            {'label': 'Pagos',
             'table': 'pagos',
             'pk': 'id_pago',
             'fields': [('id_pedido', 'int'),
                        ('id_respuesta_bold', 'int'),
                        ('monto', 'decimal'),
                        ('metodo_pago', 'str')]},
            {'label': 'Respuesta Bold',
             'table': 'respuesta_bold',
             'pk': 'id_respuesta',
             'fields': [('transaction_id', 'str'),
                        ('status', 'str'),
                        ('payment_method', 'str'),
                        ('amount', 'decimal'),
                        ('timestamp_bold', 'str'),
                        ('raw_response', 'str')]}]}
PEDIDOS_DISPLAY_QUERIES = {'pedidos': {'columns': ['id_pedido',
                         'cliente',
                         'estado',
                         'direccion',
                         'productos',
                         'subtotal',
                         'descuento',
                         'costo_envio',
                         'total',
                         'fecha_pedido'],
             'headings': ['ID', 'Cliente', 'Estado', 'Dirección', 'Productos', 'Subtotal', 'Descuento aplicado', 'Envío', 'Total', 'Fecha'],
             'select': '\n'
                       '            SELECT p.id_pedido, p.id_usuario, p.id_direccion, p.id_estado_pedido, '
                       'p.fecha_pedido,\n'
                       '                   p.subtotal, p.descuento, p.costo_envio, p.total,\n'
                       "                   CONCAT(u.nombre_usuario, ' ', u.apellido_usuario) AS cliente,\n"
                       '                   ep.descripcion_estado AS estado,\n'
                       '                   d.descripcion_direccion AS direccion,\n'
                       "                   COALESCE(productos.resumen, 'Sin productos') AS productos\n"
                       '            FROM pedidos p\n'
                       '            LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario\n'
                       '            LEFT JOIN estado_pedido ep ON ep.id_estado_pedido = p.id_estado_pedido\n'
                       '            LEFT JOIN direcciones d ON d.id_direccion = p.id_direccion\n'
                       '            LEFT JOIN (\n'
                       '                SELECT dp.id_pedido,\n'
                       "                       STRING_AGG(CONCAT(pr.nombre_producto, ' x', dp.cantidad), ', ' ORDER BY pr.nombre_producto) AS resumen\n"
                       '                FROM detalle_pedido dp\n'
                       '                LEFT JOIN variantes_producto v ON v.id_variante = dp.id_variante\n'
                       '                LEFT JOIN productos pr ON pr.id_producto = v.id_producto\n'
                       '                GROUP BY dp.id_pedido\n'
                       '            ) productos ON productos.id_pedido = p.id_pedido\n'
                       '        ',
             'search': ['CAST(p.id_pedido AS TEXT)',
                        'u.nombre_usuario',
                        'u.apellido_usuario',
                        'ep.descripcion_estado',
                        'd.descripcion_direccion',
                        'productos.resumen',
                        'CAST(p.total AS TEXT)',
                        'CAST(p.fecha_pedido AS TEXT)'],
             'order': 'p.id_pedido'},
 'detalle_pedido': {'columns': ['pedido', 'producto', 'sku', 'cantidad', 'precio_unitario'],
                    'headings': ['Pedido', 'Producto', 'SKU', 'Cantidad', 'Precio unitario'],
                    'select': '\n'
                              '            SELECT dp.id_detalle_pedido, dp.id_pedido, dp.id_variante, dp.cantidad, '
                              'dp.precio_unitario,\n'
                              "                   CONCAT('Pedido ', dp.id_pedido) AS pedido,\n"
                              '                   p.nombre_producto AS producto,\n'
                              '                   v.sku AS sku\n'
                              '            FROM detalle_pedido dp\n'
                              '            LEFT JOIN variantes_producto v ON v.id_variante = dp.id_variante\n'
                              '            LEFT JOIN productos p ON p.id_producto = v.id_producto\n'
                              '        ',
                    'search': ['CAST(dp.id_pedido AS TEXT)',
                               'p.nombre_producto',
                               'v.sku',
                               'CAST(dp.cantidad AS TEXT)',
                               'CAST(dp.precio_unitario AS TEXT)'],
                    'order': 'dp.id_detalle_pedido'},
 'estado_pedido': {'columns': ['descripcion_estado'],
                   'headings': ['Estado de pedido'],
                   'select': 'SELECT id_estado_pedido, descripcion_estado FROM estado_pedido',
                   'search': ['descripcion_estado'],
                   'order': 'id_estado_pedido'},
 'pagos': {'columns': ['pedido', 'monto', 'metodo_pago', 'fecha_pago', 'transaccion'],
           'headings': ['Pedido', 'Monto', 'Método', 'Fecha', 'Transacción'],
           'select': '\n'
                     '            SELECT pa.id_pago, pa.id_pedido, pa.id_respuesta_bold, pa.monto, pa.fecha_pago, '
                     'pa.metodo_pago,\n'
                     "                   CONCAT('Pedido ', pa.id_pedido, ' - $', p.total) AS pedido,\n"
                     '                   rb.transaction_id AS transaccion\n'
                     '            FROM pagos pa\n'
                     '            LEFT JOIN pedidos p ON p.id_pedido = pa.id_pedido\n'
                     '            LEFT JOIN respuesta_bold rb ON rb.id_respuesta = pa.id_respuesta_bold\n'
                     '        ',
           'search': ['CAST(pa.id_pedido AS TEXT)',
                      'CAST(pa.monto AS TEXT)',
                      'pa.metodo_pago',
                      'CAST(pa.fecha_pago AS TEXT)',
                      'rb.transaction_id'],
           'order': 'pa.id_pago'},
 'respuesta_bold': {'columns': ['transaction_id', 'status', 'payment_method', 'amount', 'timestamp_bold'],
                    'headings': ['Transacción', 'Estado', 'Método', 'Monto', 'Fecha Bold'],
                    'select': 'SELECT id_respuesta, transaction_id, status, payment_method, amount, timestamp_bold, '
                              'raw_response FROM respuesta_bold',
                    'search': ['transaction_id',
                               'status',
                               'payment_method',
                               'CAST(amount AS TEXT)',
                               'CAST(timestamp_bold AS TEXT)'],
                    'order': 'id_respuesta'}}


class PedidosView(BaseCrudView):
    def __init__(self):
        self.order_item_rows = []
        self.order_items_column = None
        self.variant_prices = {}
        self.variant_labels = {}
        self.subtotal_control = None
        self.discount_total_control = None
        self.total_control = None
        self.shipping_control = None
        self.controller = PedidosController()
        super().__init__(self.controller.group_id, PEDIDOS_GROUP, PEDIDOS_DISPLAY_QUERIES)

    def _load_display_table(self, config):
        if config["table"] != "pedidos":
            return super()._load_display_table(config)
        spec = self.display_queries["pedidos"]
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = " WHERE " + " OR ".join(f"{col} ILIKE :search" if not col.startswith("CAST(") else f"{col} ILIKE :search" for col in spec["search"])
            params["search"] = f"%{search_value}%"
        sql = f"{spec['select']} {where_sql} ORDER BY {spec['order']} DESC LIMIT 35"
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar pedidos", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])

        rows = []
        for item in rows_data:
            record = dict(item)
            rows.append(
                ft.DataRow(
                    cells=[
                        self._order_action_cell(record),
                        self._text_cell(record.get("id_pedido")),
                        self._text_cell(record.get("cliente")),
                        ft.DataCell(self._order_state_menu(record)),
                        self._text_cell(record.get("direccion")),
                        self._text_cell(record.get("productos")),
                        self._text_cell(record.get("subtotal")),
                        self._text_cell(record.get("descuento")),
                        self._text_cell(record.get("costo_envio")),
                        self._text_cell(record.get("total")),
                        self._text_cell(record.get("fecha_pedido")),
                    ]
                )
            )
        return self._table_panel(f"{len(rows_data)} registros", ["Acciones"] + spec["headings"], rows)

    def _order_action_cell(self, record):
        return ft.DataCell(
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_ROUNDED,
                        icon_color=Tema.GOLD,
                        tooltip="Editar",
                        on_click=lambda _, rec=record: self._edit_record(rec),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_color=Tema.ERROR,
                        tooltip="Eliminar",
                        on_click=lambda _, rec=record: self._confirm_delete(rec),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.RECEIPT_LONG_ROUNDED,
                        icon_color=Tema.INFO,
                        tooltip="Ver factura",
                        on_click=lambda _, rec=record: self._open_invoice(rec),
                    ),
                ],
            )
        )

    def _open_invoice(self, record):
        order_id = record.get("id_pedido")
        if not order_id:
            self._snack("No se pudo identificar el pedido", Tema.WARNING)
            return
        try:
            db = SessionLocal()
            try:
                pedido = (
                    db.query(Pedido)
                    .options(
                        joinedload(Pedido.usuario),
                        joinedload(Pedido.direccion),
                        joinedload(Pedido.estado),
                        joinedload(Pedido.pago),
                        joinedload(Pedido.detalles)
                        .joinedload(DetallePedido.variante)
                        .joinedload(VarianteProducto.producto),
                        joinedload(Pedido.detalles)
                        .joinedload(DetallePedido.variante)
                        .joinedload(VarianteProducto.medida),
                        joinedload(Pedido.detalles)
                        .joinedload(DetallePedido.variante)
                        .joinedload(VarianteProducto.color),
                    )
                    .filter(Pedido.id_pedido == int(order_id))
                    .one_or_none()
                )
                if not pedido:
                    raise ValueError("Pedido no encontrado")
                invoice_path = generate_invoice_pdf(pedido)
            finally:
                db.close()
            os.startfile(str(invoice_path))
            self._snack("Factura abierta correctamente", Tema.SUCCESS)
        except Exception as exc:
            self._show_message("No se pudo abrir la factura", str(exc), Tema.ERROR)

    def _order_state_options(self):
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text("SELECT id_estado_pedido, descripcion_estado FROM estado_pedido ORDER BY id_estado_pedido")).mappings().all()
            finally:
                db.close()
        except Exception:
            return []
        return [ft.dropdown.Option(key=str(row["id_estado_pedido"]), text=row["descripcion_estado"]) for row in rows]

    def _order_state_menu(self, record):
        current_state_id = str(record.get("id_estado_pedido") or "")
        items = []
        for option in self._order_state_options():
            items.append(
                ft.PopupMenuItem(
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.CHECK_ROUNDED if option.key == current_state_id else ft.Icons.CIRCLE_OUTLINED, color=Tema.GOLD if option.key == current_state_id else Tema.TEXT_MUTED, size=16),
                            ft.Text(option.text, size=12, color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.W_700 if option.key == current_state_id else ft.FontWeight.W_500),
                        ],
                    ),
                    height=38,
                    on_click=lambda _, rec=record, state_id=option.key, state_text=option.text: self._confirm_order_state_change(rec, state_id, state_text),
                )
            )
        return ft.PopupMenuButton(
            menu_position=ft.PopupMenuPosition.UNDER,
            bgcolor="#FFFFFF",
            elevation=10,
            items=items,
            content=ft.Container(
                width=152,
                border_radius=9,
                bgcolor=self._order_state_bg(record.get("estado")),
                border=ft.Border(
                    left=ft.BorderSide(1, self._order_state_border(record.get("estado"))),
                    right=ft.BorderSide(1, self._order_state_border(record.get("estado"))),
                    top=ft.BorderSide(1, self._order_state_border(record.get("estado"))),
                    bottom=ft.BorderSide(1, self._order_state_border(record.get("estado"))),
                ),
                padding=ft.Padding(10, 7, 8, 7),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(record.get("estado") or "Sin estado", size=12, color=self._order_state_color(record.get("estado")), weight=ft.FontWeight.W_800, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=16, color=self._order_state_color(record.get("estado"))),
                    ],
                ),
            ),
        )

    def _order_state_color(self, state):
        if state in ("Cancelado", "Reembolsado"):
            return Tema.ERROR
        if state in ("Entregado", "Pagado"):
            return Tema.SUCCESS
        if state in ("Despachado",):
            return Tema.INFO
        return Tema.GOLD_DARK

    def _order_state_bg(self, state):
        return ft.Colors.with_opacity(0.10, self._order_state_color(state))

    def _order_state_border(self, state):
        return ft.Colors.with_opacity(0.24, self._order_state_color(state))

    def _confirm_order_state_change(self, record, state_id, description):
        if not state_id or int(state_id) == int(record.get("id_estado_pedido") or 0):
            return
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            elevation=18,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=10, controls=[
                        ft.Icon(ft.Icons.SWAP_HORIZ_ROUNDED, color=Tema.INFO),
                        ft.Text("Cambiar estado", color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.W_800),
                    ]),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, tooltip="Cerrar", on_click=lambda _: self._close_dialog(dialog)),
                ],
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text("Confirma el nuevo estado del pedido.", size=13, color=Tema.TEXT_SECONDARY),
                        ft.Container(
                            bgcolor="#F8FAFC",
                            border_radius=8,
                            padding=ft.Padding(12, 10, 12, 10),
                            border=ft.Border(left=ft.BorderSide(3, self._order_state_color(description))),
                            content=ft.Text(f"Pedido #{record.get('id_pedido')} -> {description}", size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY, selectable=True),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Confirmar",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=lambda _: self._update_order_state_from_menu(dialog, record, state_id),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: Tema.INFO, ft.ControlState.HOVERED: "#1D5ED8"},
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialog.open = True
        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)
        self.page.update()

    def _update_order_state_from_menu(self, dialog, record, state_id):
        self._close_dialog(dialog)
        self._update_order_state(record, state_id)

    def _update_order_state(self, record, state_id):
        if not state_id:
            return
        order_id = record.get("id_pedido")
        try:
            db = SessionLocal()
            try:
                description = db.execute(
                    text("SELECT descripcion_estado FROM estado_pedido WHERE id_estado_pedido = :id"),
                    {"id": int(state_id)},
                ).scalar()
                if not description:
                    raise ValueError("Estado no encontrado")
                if description in ("Pagado", "Despachado"):
                    SalesController(db).approve_payment(order_id, estado_destino=description)
                else:
                    db.execute(
                        text("UPDATE pedidos SET id_estado_pedido = :state_id WHERE id_pedido = :order_id"),
                        {"state_id": int(state_id), "order_id": order_id},
                    )
                    db.commit()
            finally:
                db.close()
            self._build_crud_content()
            self._snack("Estado del pedido actualizado", Tema.SUCCESS)
        except Exception as exc:
            self._build_crud_content()
            self._show_message("Error al cambiar estado", str(exc), Tema.ERROR)

    def _build_form_rows(self):
        if self.current_config["table"] != "pedidos":
            return super()._build_form_rows()
        self.form_controls = {}
        self.order_item_rows = []
        self.variant_prices = self._variant_price_map()
        self.variant_labels = {key: data["label"] for key, data in self.variant_prices.items()}

        for field_name, field_type in self.current_config["fields"]:
            if field_name in ("subtotal", "descuento", "total"):
                continue
            control = self._build_field_control(field_name, field_type)
            if field_name == "costo_envio":
                self.shipping_control = control
                control.on_change = lambda _: self._recalculate_order_totals()
            self.form_controls[field_name] = control

        if "id_usuario" in self.form_controls:
            self.form_controls["id_usuario"].on_select = lambda _: self._set_default_address_for_selected_user()
            self.form_controls["id_usuario"].on_change = lambda _: self._set_default_address_for_selected_user()

        self.subtotal_control = self._money_summary_field("Subtotal")
        self.discount_total_control = self._money_summary_field("Descuento")
        self.total_control = self._money_summary_field("Total")
        self.form_controls["subtotal"] = self.subtotal_control
        self.form_controls["descuento"] = self.discount_total_control
        self.form_controls["total"] = self.total_control

        self.order_items_column = ft.Column(spacing=8)
        self._add_order_item_row()

        return [
            ft.ResponsiveRow(spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "md": 6}, content=self.form_controls["id_usuario"]),
                ft.Container(col={"xs": 12, "md": 6}, content=self.form_controls["id_direccion"]),
                ft.Container(col={"xs": 12, "md": 6}, content=self.form_controls["id_estado_pedido"]),
                ft.Container(col={"xs": 12, "md": 6}, content=self.form_controls["costo_envio"]),
            ]),
            self._order_items_panel(),
            ft.ResponsiveRow(spacing=12, run_spacing=12, controls=[
                ft.Container(col={"xs": 12, "md": 4}, content=self.subtotal_control),
                ft.Container(col={"xs": 12, "md": 4}, content=self.discount_total_control),
                ft.Container(col={"xs": 12, "md": 4}, content=self.total_control),
            ]),
        ]

    def _set_default_address_for_selected_user(self):
        user_id = self._field_value("id_usuario") if "id_usuario" in self.form_controls else None
        if not user_id:
            return
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return
        address_control = self.form_controls.get("id_direccion")
        if address_control is None:
            return
        try:
            db = SessionLocal()
            try:
                row = db.execute(text("""
                    SELECT id_direccion
                    FROM direcciones
                    WHERE id_usuario = :user_id
                    ORDER BY es_principal DESC, id_direccion DESC
                    LIMIT 1
                """), {"user_id": user_id}).mappings().first()
            finally:
                db.close()
        except Exception:
            return
        if not row:
            address_control.value = ""
            self._snack("Este usuario no tiene direcciones registradas", Tema.WARNING)
        else:
            address_control.value = str(row["id_direccion"])
        try:
            address_control.update()
        except RuntimeError:
            pass

    def _money_summary_field(self, label):
        return ft.TextField(
            label=label,
            value="0.00",
            read_only=True,
            dense=True,
            prefix_icon=ft.Icons.ATTACH_MONEY_ROUNDED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#F8FAFC",
            color=Tema.TEXT_PRIMARY,
        )

    def _order_items_panel(self):
        return ft.Container(
            bgcolor=Tema.GOLD_SOFT,
            border_radius=10,
            padding=14,
            border=ft.Border(
                left=ft.BorderSide(4, Tema.GOLD),
                right=ft.BorderSide(1, "#F7D08A"),
                top=ft.BorderSide(1, "#F7D08A"),
                bottom=ft.BorderSide(1, "#F7D08A"),
            ),
            content=ft.Column(spacing=10, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text("Productos del pedido", size=15, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                            ft.Text("Agrega productos como en una mini hoja de cálculo.", size=12, color=Tema.TEXT_MUTED),
                        ]),
                        ft.FilledButton(
                            "Agregar producto",
                            icon=ft.Icons.ADD_ROUNDED,
                            on_click=lambda _: self._add_order_item_row(),
                            style=ft.ButtonStyle(
                                bgcolor={ft.ControlState.DEFAULT: Tema.GOLD, ft.ControlState.HOVERED: Tema.GOLD_DARK},
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=9),
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor=Tema.BG_CARD,
                    border_radius=8,
                    padding=ft.Padding(10, 8, 10, 8),
                    content=ft.Row(spacing=8, controls=[
                        ft.Container(width=330, content=ft.Text("Producto", size=12, weight=ft.FontWeight.W_800, color=Tema.TEXT_SECONDARY)),
                        ft.Container(width=78, content=ft.Text("Cant.", size=12, weight=ft.FontWeight.W_800, color=Tema.TEXT_SECONDARY)),
                        ft.Container(width=108, content=ft.Text("Precio", size=12, weight=ft.FontWeight.W_800, color=Tema.TEXT_SECONDARY)),
                        ft.Container(width=160, content=ft.Text("Descuento", size=12, weight=ft.FontWeight.W_800, color=Tema.TEXT_SECONDARY)),
                        ft.Container(width=118, content=ft.Text("Total línea", size=12, weight=ft.FontWeight.W_800, color=Tema.TEXT_SECONDARY)),
                        ft.Container(width=40, content=ft.Text("", size=12)),
                    ]),
                ),
                self.order_items_column,
            ]),
        )

    def _variant_price_map(self):
        data = {}
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text("""
                    SELECT v.id_variante, v.sku, v.referencia, v.precio, v.stock,
                           p.nombre_producto, c.nombre_color, m.nombre_medida
                    FROM variantes_producto v
                    JOIN productos p ON p.id_producto = v.id_producto
                    LEFT JOIN colores c ON c.id_color = v.id_color
                    LEFT JOIN medidas m ON m.id_medida = v.id_medida
                    WHERE v.estado = TRUE AND p.estado_producto = TRUE AND v.stock > 0
                    ORDER BY p.nombre_producto ASC, v.sku ASC
                    LIMIT 300
                """)).mappings().all()
            finally:
                db.close()
        except Exception:
            return data
        for row in rows:
            key = str(row["id_variante"])
            extra = " / ".join(str(row[col]) for col in ("nombre_medida", "nombre_color") if row.get(col))
            label = f"{row['nombre_producto']} - {row['sku']}"
            if extra:
                label += f" - {extra}"
            label += f" - ${float(row['precio'] or 0):,.0f} - Stock {row['stock']}"
            data[key] = {"price": Decimal(row["precio"] or 0), "label": label, "stock": int(row["stock"] or 0)}
        return data

    def _variant_options(self):
        options = [ft.dropdown.Option(key="", text="Selecciona producto")]
        for key, data in self.variant_prices.items():
            options.append(ft.dropdown.Option(key=key, text=data["label"]))
        return options


    def _discount_options(self):
        options = [ft.dropdown.Option(key="0", text="Sin descuento")]
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
                rows = db.execute(text("""
                    SELECT d.id, d.codigo, d.porcentaje_descuento, p.nombre_producto
                    FROM descuentos d
                    LEFT JOIN productos p ON p.id_producto = d.id_producto
                    WHERE d.is_active = TRUE
                      AND CURRENT_DATE BETWEEN d.fecha_inicio AND d.fecha_fin
                    ORDER BY d.porcentaje_descuento DESC, d.codigo ASC
                """)).mappings().all()
            finally:
                db.close()
        except Exception:
            return options
        for row in rows:
            product = row["nombre_producto"] or "Global"
            percent = Decimal(row["porcentaje_descuento"] or 0)
            options.append(ft.dropdown.Option(key=str(percent), text=f"{row['codigo']} - {percent}% - {product}"))
        return options

    def _line_discount_options(self):
        return [
            ft.dropdown.Option(key="0", text="Sin descuento"),
            *self._discount_options()[1:],
        ]

    def _add_order_item_row(self):
        row = {}
        product = ft.Dropdown(
            width=330,
            dense=True,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=240,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            options=self._variant_options(),
            hint_text="Producto",
        )
        qty = ft.TextField(value="1", width=78, dense=True, text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor="#FFFFFF", color=Tema.TEXT_PRIMARY)
        price = ft.TextField(value="0.00", width=108, dense=True, read_only=True, border_color=Tema.BORDER, bgcolor=Tema.BG_TABLE_HEAD, color=Tema.TEXT_PRIMARY)
        discount = ft.Dropdown(width=160, dense=True, editable=True, enable_filter=True, enable_search=True, menu_height=220, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor="#FFFFFF", color=Tema.TEXT_PRIMARY, options=self._line_discount_options(), value="0")
        line_total = ft.TextField(value="0.00", width=118, dense=True, read_only=True, border_color=Tema.BORDER, bgcolor=Tema.BG_TABLE_HEAD, color=Tema.TEXT_PRIMARY)

        row.update({"product": product, "qty": qty, "price": price, "discount": discount, "line_total": line_total})
        product.on_select = lambda _, current=row: self._on_variant_selected(current)
        qty.on_change = lambda _: self._recalculate_order_totals()
        discount.on_select = lambda _: self._recalculate_order_totals()

        remove = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=Tema.ERROR, tooltip="Quitar producto", on_click=lambda _, current=row: self._remove_order_item_row(current))
        row["control"] = ft.Container(
            bgcolor="#FFFFFF",
            border_radius=8,
            padding=ft.Padding(10, 8, 10, 8),
            border=ft.Border(bottom=ft.BorderSide(1, "#EEF2F6")),
            content=ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[product, qty, price, discount, line_total, remove]),
        )
        self.order_item_rows.append(row)
        if self.order_items_column is not None:
            self.order_items_column.controls.append(row["control"])
            self._recalculate_order_totals()
            try:
                self.order_items_column.update()
            except RuntimeError:
                pass

    def _remove_order_item_row(self, row):
        if len(self.order_item_rows) <= 1:
            row["product"].value = ""
            row["qty"].value = "1"
            row["price"].value = "0.00"
            row["discount"].value = "0"
            row["line_total"].value = "0.00"
        else:
            self.order_item_rows.remove(row)
            if row["control"] in self.order_items_column.controls:
                self.order_items_column.controls.remove(row["control"])
        self._recalculate_order_totals()
        try:
            self.order_items_column.update()
        except RuntimeError:
            pass

    def _on_variant_selected(self, row):
        data = self.variant_prices.get(str(row["product"].value))
        row["price"].value = f"{(data['price'] if data else Decimal('0')):.2f}"
        self._recalculate_order_totals()

    def _decimal_from_control(self, control):
        try:
            return Decimal(str(control.value or "0").replace(",", ""))
        except Exception:
            return Decimal("0")

    def _recalculate_order_totals(self):
        subtotal = Decimal("0")
        discount_total = Decimal("0")
        for row in self.order_item_rows:
            price = self._decimal_from_control(row["price"])
            try:
                qty = max(0, int(str(row["qty"].value or "0")))
            except Exception:
                qty = 0
            percent = self._decimal_from_control(row["discount"])
            gross = price * qty
            line_discount = (gross * percent / Decimal("100")).quantize(Decimal("0.01"))
            total_line = gross - line_discount
            subtotal += gross
            discount_total += line_discount
            row["line_total"].value = f"{total_line:.2f}"
        shipping = self._decimal_from_control(self.shipping_control) if self.shipping_control else Decimal("0")
        total = subtotal - discount_total + shipping
        if self.subtotal_control:
            self.subtotal_control.value = f"{subtotal:.2f}"
        if self.discount_total_control:
            self.discount_total_control.value = f"{discount_total:.2f}"
        if self.total_control:
            self.total_control.value = f"{total:.2f}"
        try:
            self.page.update()
        except RuntimeError:
            pass

    def _save_record(self, dialog=None):
        if self.current_config["table"] != "pedidos":
            return self.controller.save_record(self, dialog)
        try:
            self._clear_dialog_error()
            self._recalculate_order_totals()
            values = {
                "id_usuario": self._parse_value(self._field_value("id_usuario"), "int"),
                "id_direccion": self._parse_value(self._field_value("id_direccion"), "int"),
                "id_estado_pedido": self._parse_value(self._field_value("id_estado_pedido"), "int"),
                "subtotal": self._decimal_from_control(self.subtotal_control),
                "descuento": self._decimal_from_control(self.discount_total_control),
                "costo_envio": self._decimal_from_control(self.shipping_control),
                "total": self._decimal_from_control(self.total_control),
            }
            for required in ("id_usuario", "id_direccion", "id_estado_pedido"):
                if values[required] in (None, ""):
                    raise ValueError(f"El campo {self._pretty(required)} es obligatorio")
            details = []
            requested_stock = {}
            for row in self.order_item_rows:
                variant_id = row["product"].value
                if not variant_id:
                    continue
                qty = int(str(row["qty"].value or "0"))
                if qty <= 0:
                    raise ValueError("La cantidad de cada producto debe ser mayor a cero")
                variant_data = self.variant_prices.get(str(variant_id))
                if not variant_data:
                    raise ValueError("El producto seleccionado ya no está disponible")
                requested_stock[str(variant_id)] = requested_stock.get(str(variant_id), 0) + qty
                if requested_stock[str(variant_id)] > variant_data["stock"]:
                    raise ValueError(f"Stock insuficiente para {variant_data['label']}. Disponible: {variant_data['stock']}")
                price = self._decimal_from_control(row["price"])
                percent = self._decimal_from_control(row["discount"])
                unit_price = (price * (Decimal("1") - (percent / Decimal("100")))).quantize(Decimal("0.01"))
                details.append({"id_variante": int(variant_id), "cantidad": qty, "precio_unitario": unit_price})
            if not details:
                raise ValueError("Agrega al menos un producto al pedido")
            db = SessionLocal()
            try:
                if self.selected_record_id is None:
                    result = db.execute(text("""
                        INSERT INTO pedidos (id_usuario, id_direccion, id_estado_pedido, subtotal, descuento, costo_envio, total)
                        VALUES (:id_usuario, :id_direccion, :id_estado_pedido, :subtotal, :descuento, :costo_envio, :total)
                        RETURNING id_pedido
                    """), values)
                    pedido_id = result.scalar()
                else:
                    pedido_id = self.selected_record_id
                    db.execute(text("""
                        UPDATE pedidos
                        SET id_usuario = :id_usuario,
                            id_direccion = :id_direccion,
                            id_estado_pedido = :id_estado_pedido,
                            subtotal = :subtotal,
                            descuento = :descuento,
                            costo_envio = :costo_envio,
                            total = :total
                        WHERE id_pedido = :id_pedido
                    """), {**values, "id_pedido": pedido_id})
                    db.execute(text("DELETE FROM detalle_pedido WHERE id_pedido = :id_pedido"), {"id_pedido": pedido_id})
                for detail in details:
                    db.execute(text("""
                        INSERT INTO detalle_pedido (id_pedido, id_variante, cantidad, precio_unitario)
                        VALUES (:id_pedido, :id_variante, :cantidad, :precio_unitario)
                    """), {"id_pedido": pedido_id, **detail})
                SalesController(db).ensure_order_stock_discounted(pedido_id)
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
            self._clear_form()
            self._build_crud_content()
            if dialog is not None:
                self._close_dialog(dialog)
            self._snack("Pedido guardado correctamente", Tema.SUCCESS)
        except Exception as exc:
            if dialog is not None:
                self._show_dialog_error(f"No se pudo guardar pedido: {exc}")
            else:
                self._snack(f"No se pudo guardar pedido: {exc}", Tema.ERROR)

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

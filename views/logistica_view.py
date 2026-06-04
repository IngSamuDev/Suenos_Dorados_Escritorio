import flet as ft
from sqlalchemy import text

from controllers.logistica_controller import LogisticaController
from controllers.ventas_controller import SalesController
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
                        ('fecha_envio', 'date'),
                        ('fecha_entrega_estimada', 'date'),
                        ('fecha_entrega_real', 'date')]},
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
                       'estado_pedido',
                       'numero_guia',
                       'transportadora',
                       'fecha_envio',
                       'fecha_entrega_estimada',
                       'fecha_entrega_real'],
           'headings': ['Pedido', 'Estado pedido', 'Guía', 'Transportadora', 'Envío', 'Entrega estimada', 'Entrega real'],
           'select': '\n'
                     '            SELECT e.id_envio, e.id_pedido, e.id_estado_envio, p.id_estado_pedido, e.numero_guia, e.transportadora,\n'
                     '                   e.fecha_envio, e.fecha_entrega_estimada, e.fecha_entrega_real,\n'
                     "                   CONCAT('Pedido #', e.id_pedido, ' - ', COALESCE(NULLIF(CONCAT(u.nombre_usuario, ' ', u.apellido_usuario), ' '), 'Sin usuario')) AS pedido,\n"
                     '                   ep.descripcion_estado AS estado_pedido,\n'
                     '                   ee.descripcion_estado AS estado_envio\n'
                     '            FROM envio e\n'
                     '            LEFT JOIN estado_envio ee ON ee.id_estado_envio = e.id_estado_envio\n'
                     '            LEFT JOIN pedidos p ON p.id_pedido = e.id_pedido\n'
                     '            LEFT JOIN estado_pedido ep ON ep.id_estado_pedido = p.id_estado_pedido\n'
                     '            LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario\n'
                     '        ',
           'search': ['CAST(e.id_pedido AS TEXT)',
                      'u.nombre_usuario',
                      'u.apellido_usuario',
                      'ep.descripcion_estado',
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

    def _build_form_rows(self):
        controls = super()._build_form_rows()
        if self.current_config["table"] == "envio" and "id_pedido" in self.form_controls:
            self.form_controls["id_pedido"].on_select = lambda _: self._set_default_shipping_state_for_selected_order()
            self.form_controls["id_pedido"].on_change = lambda _: self._set_default_shipping_state_for_selected_order()
        return controls

    def _set_default_shipping_state_for_selected_order(self):
        order_id = self._field_value("id_pedido") if "id_pedido" in self.form_controls else None
        if not order_id:
            return
        try:
            order_id = int(order_id)
        except (TypeError, ValueError):
            return
        state_control = self.form_controls.get("id_estado_envio")
        if state_control is None:
            return
        try:
            db = SessionLocal()
            try:
                state_id = db.execute(text("""
                    SELECT id_estado_envio
                    FROM envio
                    WHERE id_pedido = :order_id
                    LIMIT 1
                """), {"order_id": order_id}).scalar()
                if not state_id:
                    state_id = db.execute(text("""
                        SELECT id_estado_envio
                        FROM estado_envio
                        ORDER BY
                            CASE
                                WHEN descripcion_estado ILIKE '%pendiente%' THEN 0
                                WHEN descripcion_estado ILIKE '%prepar%' THEN 1
                                ELSE 2
                            END,
                            id_estado_envio
                        LIMIT 1
                    """)).scalar()
            finally:
                db.close()
        except Exception:
            return
        if state_id:
            state_control.value = str(state_id)
            try:
                state_control.update()
            except RuntimeError:
                pass

    def _load_display_table(self, config):
        if config["table"] != "envio":
            return super()._load_display_table(config)
        spec = self.display_queries["envio"]
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
            return self._panel([ft.Text("No se pudo cargar envíos", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])

        rows = []
        for item in rows_data:
            record = dict(item)
            rows.append(
                ft.DataRow(
                    cells=[
                        self._action_cell(record),
                        self._text_cell(record.get("pedido")),
                        ft.DataCell(self._order_state_menu(record)),
                        self._text_cell(record.get("numero_guia")),
                        self._text_cell(record.get("transportadora")),
                        self._text_cell(record.get("fecha_envio")),
                        self._text_cell(record.get("fecha_entrega_estimada")),
                        self._text_cell(record.get("fecha_entrega_real")),
                    ]
                )
            )
        return self._table_panel(f"{len(rows_data)} envíos", ["Acciones"] + spec["headings"], rows)

    def _shipping_state_options(self):
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text("SELECT id_estado_envio, descripcion_estado FROM estado_envio ORDER BY id_estado_envio")).mappings().all()
            finally:
                db.close()
        except Exception:
            return []
        return [ft.dropdown.Option(key=str(row["id_estado_envio"]), text=row["descripcion_estado"]) for row in rows]

    def _shipping_state_menu(self, record):
        current_state_id = str(record.get("id_estado_envio") or "")
        items = []
        for option in self._shipping_state_options():
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
                    on_click=lambda _, rec=record, state_id=option.key, state_text=option.text: self._confirm_shipping_state_change(rec, state_id, state_text),
                )
            )
        state_text = record.get("estado_envio") or "Sin estado"
        state_color = self._shipping_state_color(state_text)
        return ft.PopupMenuButton(
            menu_position=ft.PopupMenuPosition.UNDER,
            bgcolor="#FFFFFF",
            elevation=10,
            items=items,
            content=ft.Container(
                width=172,
                border_radius=9,
                bgcolor=ft.Colors.with_opacity(0.10, state_color),
                border=ft.Border(
                    left=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    right=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    top=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                ),
                padding=ft.Padding(10, 7, 8, 7),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(state_text, size=12, color=state_color, weight=ft.FontWeight.W_800, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=16, color=state_color),
                    ],
                ),
            ),
        )

    def _shipping_state_color(self, state):
        if state in ("Cancelado", "Novedad", "Devuelto"):
            return Tema.ERROR
        if state in ("Entregado", "Completado"):
            return Tema.SUCCESS
        if state in ("En tránsito", "Despachado", "Enviado"):
            return Tema.INFO
        return Tema.GOLD_DARK

    def _update_shipping_state(self, record, state_id):
        if not state_id or int(state_id) == int(record.get("id_estado_envio") or 0):
            return
        try:
            db = SessionLocal()
            try:
                db.execute(
                    text("UPDATE envio SET id_estado_envio = :state_id WHERE id_envio = :shipping_id"),
                    {"state_id": int(state_id), "shipping_id": record.get("id_envio")},
                )
                db.commit()
            finally:
                db.close()
            self._build_crud_content()
            self._snack("Estado del envío actualizado", Tema.SUCCESS)
        except Exception as exc:
            self._build_crud_content()
            self._show_message("Error al cambiar estado", str(exc), Tema.ERROR)

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
        state_text = record.get("estado_pedido") or "Sin estado"
        state_color = self._order_state_color(state_text)
        return ft.PopupMenuButton(
            menu_position=ft.PopupMenuPosition.UNDER,
            bgcolor="#FFFFFF",
            elevation=10,
            items=items,
            content=ft.Container(
                width=152,
                border_radius=9,
                bgcolor=ft.Colors.with_opacity(0.10, state_color),
                border=ft.Border(
                    left=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    right=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    top=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.24, state_color)),
                ),
                padding=ft.Padding(10, 7, 8, 7),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(state_text, size=12, color=state_color, weight=ft.FontWeight.W_800, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, size=16, color=state_color),
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

    def _confirm_order_state_change(self, record, state_id, description):
        if not state_id or int(state_id) == int(record.get("id_estado_pedido") or 0):
            return
        self._confirm_state_change(
            title="Cambiar estado del pedido",
            message=f"Pedido #{record.get('id_pedido')} -> {description}",
            color=self._order_state_color(description),
            on_confirm=lambda dialog: self._apply_order_state_change(dialog, record, state_id),
        )

    def _confirm_shipping_state_change(self, record, state_id, description):
        if not state_id or int(state_id) == int(record.get("id_estado_envio") or 0):
            return
        self._confirm_state_change(
            title="Cambiar estado del envío",
            message=f"{record.get('pedido')} -> {description}",
            color=self._shipping_state_color(description),
            on_confirm=lambda dialog: self._apply_shipping_state_change(dialog, record, state_id),
        )

    def _confirm_state_change(self, title, message, color, on_confirm):
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            elevation=18,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=10, controls=[
                        ft.Icon(ft.Icons.SWAP_HORIZ_ROUNDED, color=color),
                        ft.Text(title, color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.W_800),
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
                        ft.Text("Confirma el nuevo estado antes de guardar el cambio.", size=13, color=Tema.TEXT_SECONDARY),
                        ft.Container(
                            bgcolor="#F8FAFC",
                            border_radius=8,
                            padding=ft.Padding(12, 10, 12, 10),
                            border=ft.Border(left=ft.BorderSide(3, color)),
                            content=ft.Text(message, size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY, selectable=True),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Confirmar",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=lambda _: on_confirm(dialog),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: color},
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

    def _apply_shipping_state_change(self, dialog, record, state_id):
        self._close_dialog(dialog)
        self._update_shipping_state(record, state_id)

    def _apply_order_state_change(self, dialog, record, state_id):
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

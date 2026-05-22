from decimal import Decimal

import flet as ft
from sqlalchemy import text

from controllers.pedidos_controller import PedidosController
from controllers.ventas_controller import SalesController
from database import SessionLocal
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
PEDIDOS_DISPLAY_QUERIES = {'pedidos': {'columns': ['cliente',
                         'estado',
                         'direccion',
                         'subtotal',
                         'descuento',
                         'costo_envio',
                         'total',
                         'fecha_pedido'],
             'headings': ['Cliente', 'Estado', 'Dirección', 'Subtotal', 'Descuento aplicado', 'Envío', 'Total', 'Fecha'],
             'select': '\n'
                       '            SELECT p.id_pedido, p.id_usuario, p.id_direccion, p.id_estado_pedido, '
                       'p.fecha_pedido,\n'
                       '                   p.subtotal, p.descuento, p.costo_envio, p.total,\n'
                       "                   CONCAT(u.nombre_usuario, ' ', u.apellido_usuario) AS cliente,\n"
                       '                   ep.descripcion_estado AS estado,\n'
                       '                   d.descripcion_direccion AS direccion\n'
                       '            FROM pedidos p\n'
                       '            LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario\n'
                       '            LEFT JOIN estado_pedido ep ON ep.id_estado_pedido = p.id_estado_pedido\n'
                       '            LEFT JOIN direcciones d ON d.id_direccion = p.id_direccion\n'
                       '        ',
             'search': ['u.nombre_usuario',
                        'u.apellido_usuario',
                        'ep.descripcion_estado',
                        'd.descripcion_direccion',
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
            bgcolor="#FFFBEB",
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
                    bgcolor="#FFFFFF",
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
                    WHERE v.estado = TRUE AND p.estado_producto = TRUE
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
            label += f" - ${float(row['precio'] or 0):,.0f}"
            data[key] = {"price": Decimal(row["precio"] or 0), "label": label}
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
        price = ft.TextField(value="0.00", width=108, dense=True, read_only=True, border_color=Tema.BORDER, bgcolor="#F8FAFC", color=Tema.TEXT_PRIMARY)
        discount = ft.Dropdown(width=160, dense=True, editable=True, enable_filter=True, enable_search=True, menu_height=220, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor="#FFFFFF", color=Tema.TEXT_PRIMARY, options=self._line_discount_options(), value="0")
        line_total = ft.TextField(value="0.00", width=118, dense=True, read_only=True, border_color=Tema.BORDER, bgcolor="#F8FAFC", color=Tema.TEXT_PRIMARY)

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
            for row in self.order_item_rows:
                variant_id = row["product"].value
                if not variant_id:
                    continue
                qty = int(str(row["qty"].value or "0"))
                if qty <= 0:
                    raise ValueError("La cantidad de cada producto debe ser mayor a cero")
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

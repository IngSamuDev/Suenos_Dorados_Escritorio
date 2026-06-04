import uuid
from decimal import Decimal

import flet as ft
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from database import SessionLocal
from models.ventas_model import Pedido
from services.bold_payments_service import process_bold_payment
from utils.theme import Tema


def _border(color):
    return ft.Border(
        left=ft.BorderSide(1, color),
        right=ft.BorderSide(1, color),
        top=ft.BorderSide(1, color),
        bottom=ft.BorderSide(1, color),
    )


class BoldPaymentsView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.bgcolor = Tema.BG_PRIMARY
        self.orders = []
        self.selected_order_id = None
        self.status_text = ft.Text("", size=12, color=Tema.TEXT_MUTED)
        self.selected_label = ft.Text("Selecciona un pedido de la tabla", size=12, color=Tema.TEXT_MUTED)
        self.orders_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Cliente")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Pago")),
            ],
            rows=[],
            heading_row_color=Tema.BG_TABLE_HEAD,
            border=_border(Tema.BORDER),
            border_radius=8,
            column_spacing=24,
        )
        self.content = ft.Column(
            expand=True,
            spacing=14,
            controls=[
                self._header_panel(),
                self._simulator_panel(),
                ft.Container(expand=True, content=self._orders_panel()),
            ],
        )

    def did_mount(self):
        self.load_orders()

    def _header_panel(self):
        return ft.Container(
            bgcolor=Tema.BG_CARD,
            border_radius=8,
            padding=18,
            border=_border(Tema.BORDER_SOFT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(spacing=4, controls=[
                        ft.Text("Pagos Bold", size=18, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                        ft.Text("Consulta pedidos y simula webhooks seguros de la pasarela.", size=12, color=Tema.TEXT_MUTED),
                    ]),
                    ft.FilledButton(
                        "Sincronizar",
                        icon=ft.Icons.SYNC_ROUNDED,
                        on_click=lambda _: self.load_orders(),
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: Tema.GOLD, ft.ControlState.HOVERED: Tema.GOLD_DARK},
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    ),
                ],
            ),
        )

    def _simulator_panel(self):
        return ft.Container(
            bgcolor=Tema.BG_CARD,
            border_radius=8,
            padding=18,
            border=_border(Tema.BORDER_SOFT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                controls=[
                    ft.Column(spacing=5, controls=[
                        ft.Text("Simular Pago Bold", size=16, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                        self.selected_label,
                    ]),
                    ft.Row(spacing=10, controls=[
                        ft.FilledButton(
                            "Aprobar",
                            icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                            on_click=lambda _: self.simulate_payment("APPROVED"),
                            style=ft.ButtonStyle(bgcolor={ft.ControlState.DEFAULT: Tema.SUCCESS}, color=ft.Colors.WHITE),
                        ),
                        ft.OutlinedButton(
                            "Rechazar",
                            icon=ft.Icons.CANCEL_ROUNDED,
                            on_click=lambda _: self.simulate_payment("REJECTED"),
                            style=ft.ButtonStyle(color=Tema.ERROR, side={ft.ControlState.DEFAULT: ft.BorderSide(1, Tema.ERROR)}),
                        ),
                    ]),
                ],
            ),
        )

    def _orders_panel(self):
        return ft.Container(
            expand=True,
            bgcolor=Tema.BG_CARD,
            border_radius=8,
            padding=18,
            border=_border(Tema.BORDER_SOFT),
            content=ft.Column(expand=True, spacing=12, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Pedidos sincronizados", size=15, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                        self.status_text,
                    ],
                ),
                ft.Row(expand=True, scroll=ft.ScrollMode.AUTO, controls=[self.orders_table]),
            ]),
        )

    def _set_status(self, message, color=Tema.TEXT_MUTED):
        self.status_text.value = message
        self.status_text.color = color
        try:
            self.update()
        except RuntimeError:
            pass

    def load_orders(self):
        try:
            db = SessionLocal()
            try:
                orders = (
                    db.query(Pedido)
                    .options(joinedload(Pedido.usuario), joinedload(Pedido.estado), joinedload(Pedido.pago))
                    .order_by(Pedido.id_pedido.desc())
                    .limit(60)
                    .all()
                )
                self.orders = [self._serialize_order(order) for order in orders]
            finally:
                db.close()
            self._build_rows()
            self._set_status(f"{len(self.orders)} pedidos sincronizados", Tema.SUCCESS)
        except Exception as exc:
            self._set_status(f"Error cargando pedidos: {exc}", Tema.ERROR)

    def _serialize_order(self, order):
        user = order.usuario
        client = " ".join(
            part for part in [
                getattr(user, "nombre_usuario", ""),
                getattr(user, "apellido_usuario", ""),
            ] if part
        ).strip() or "Sin cliente"
        return {
            "id_pedido": order.id_pedido,
            "cliente": client,
            "total": str(order.total or 0),
            "id_estado_pedido": order.id_estado_pedido,
            "estado": order.estado.descripcion_estado if order.estado else "Sin estado",
            "pago_status": "PAGADO" if order.pago else "PENDIENTE",
        }

    def _build_rows(self):
        self.orders_table.rows.clear()
        for order in self.orders:
            order_id = int(order["id_pedido"])
            self.orders_table.rows.append(
                ft.DataRow(
                    selected=self.selected_order_id == order_id,
                    on_select_change=lambda _, oid=order_id: self._select_order(oid),
                    cells=[
                        ft.DataCell(ft.Text(f"#{order_id}", weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY)),
                        ft.DataCell(ft.Text(order["cliente"], color=Tema.TEXT_PRIMARY)),
                        ft.DataCell(ft.Text(f"${Decimal(str(order['total'])):,.0f}", color=Tema.TEXT_PRIMARY)),
                        ft.DataCell(self._state_badge(int(order["id_estado_pedido"]), order["estado"])),
                        ft.DataCell(ft.Text(order.get("pago_status", "PENDIENTE"), color=Tema.TEXT_SECONDARY)),
                    ],
                )
            )

    def _select_order(self, order_id):
        self.selected_order_id = order_id
        self.selected_label.value = f"Pedido seleccionado: #{order_id}"
        self._build_rows()
        try:
            self.update()
        except RuntimeError:
            pass

    def _state_badge(self, state_id, label):
        palette = {
            1: (Tema.GOLD_SOFT, Tema.GOLD_DARK),
            2: (ft.Colors.with_opacity(0.12, Tema.SUCCESS), Tema.SUCCESS),
            3: (Tema.GOLD_SOFT, Tema.GOLD_DARK),
            4: (ft.Colors.with_opacity(0.12, Tema.INFO), Tema.INFO),
            5: (ft.Colors.with_opacity(0.12, Tema.SUCCESS), Tema.SUCCESS),
            6: (ft.Colors.with_opacity(0.12, Tema.ERROR), Tema.ERROR),
            7: (ft.Colors.with_opacity(0.12, Tema.ERROR), Tema.ERROR),
        }
        bg_color, text_color = palette.get(state_id, (Tema.BG_TABLE_HEAD, Tema.TEXT_SECONDARY))
        return ft.Container(
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=20,
            bgcolor=bg_color,
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_800, color=text_color),
        )

    def simulate_payment(self, status):
        if self.selected_order_id is None:
            self._set_status("Selecciona primero un pedido", Tema.WARNING)
            return
        order = next((item for item in self.orders if int(item["id_pedido"]) == self.selected_order_id), None)
        if not order:
            self._set_status("No se encontro el pedido seleccionado", Tema.ERROR)
            return
        payload = {
            "transaction_id": f"SIM-{uuid.uuid4().hex[:12].upper()}",
            "order_id": self.selected_order_id,
            "status": status,
            "amount": str(order["total"]),
            "payment_method": "Bold Sandbox",
        }
        try:
            result = self._process_bold_payment(payload)
            self._set_status(result.get("message", "Webhook procesado"), Tema.SUCCESS if result.get("ok") else Tema.WARNING)
            self.load_orders()
        except Exception as exc:
            self._set_status(f"Error simulando pago: {exc}", Tema.ERROR)

    def _process_bold_payment(self, payload):
        db = SessionLocal()
        try:
            return process_bold_payment(db, payload)
        except IntegrityError as exc:
            db.rollback()
            detail = getattr(getattr(exc, "orig", None), "diag", None)
            constraint = getattr(detail, "constraint_name", None) if detail else None
            if constraint == "respuesta_bold_id_pedido_not_null":
                raise ValueError("No se pudo asociar la respuesta de Bold al pedido") from exc
            raise ValueError(f"Conflicto de integridad en pagos Bold: {constraint or exc.orig}") from exc
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

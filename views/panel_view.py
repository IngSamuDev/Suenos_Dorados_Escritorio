import flet as ft
from sqlalchemy import text

from config import APP_NAME, APP_SUBTITLE, LOGO_FILE
from views.descuentos_view import DescuentosView
from views.logistica_view import LogisticaView
from views.pedidos_view import PedidosView
from views.catalogo_view import CatalogoView
from views.productos_view import (
    ColeccionesView,
    ColoresView,
    ImagenesView,
    InventarioView,
    MedidasView,
    ProductosView,
)
from views.usuarios_view import UsuariosView
from views.empresa_view import EmpresaView
from controllers.catalogo_controller import CatalogController
from controllers.inventario_controller import InventoryController
from controllers.ventas_controller import SalesController
from controllers.empresa_controller import EmpresaController
from database import SessionLocal
from utils.theme import Tema


class DashboardView(ft.Container):
    DESTINATIONS = [
        ("Dashboard", ft.Icons.DASHBOARD_ROUNDED, "dashboard"),
        ("Usuarios", ft.Icons.PEOPLE_ROUNDED, "usuarios"),
        ("Productos", ft.Icons.CATEGORY_ROUNDED, "productos"),
        ("Descuentos", ft.Icons.LOCAL_OFFER_ROUNDED, "descuentos"),
        ("Medidas", ft.Icons.STRAIGHTEN_ROUNDED, "medidas"),
        ("Colores", ft.Icons.PALETTE_ROUNDED, "colores"),
        ("Imágenes", ft.Icons.IMAGE_ROUNDED, "imagenes"),
        ("Catálogo", ft.Icons.INVENTORY_2_ROUNDED, "catalogo"),
        ("Colecciones", ft.Icons.COLLECTIONS_BOOKMARK_ROUNDED, "colecciones"),
        ("Inventario", ft.Icons.WAREHOUSE_ROUNDED, "inventario"),
        ("Pedidos", ft.Icons.RECEIPT_LONG_ROUNDED, "pedidos"),
        ("Logística", ft.Icons.LOCAL_SHIPPING_ROUNDED, "logistica"),
        ("Configuración", ft.Icons.SETTINGS_ROUNDED, "empresa"),
    ]

    VIEW_FACTORY = {
        "usuarios": UsuariosView,
        "productos": ProductosView,
        "descuentos": DescuentosView,
        "medidas": MedidasView,
        "colores": ColoresView,
        "imagenes": ImagenesView,
        "catalogo": CatalogoView,
        "colecciones": ColeccionesView,
        "inventario": InventarioView,
        "pedidos": PedidosView,
        "logistica": LogisticaView,
        "empresa": EmpresaView,
    }

    def __init__(self, usuario, on_logout):
        super().__init__()
        self.usuario = usuario
        self.on_logout = on_logout
        self.selected_index = 0
        self.empresa_controller = EmpresaController()
        self.empresa_info = self.empresa_controller.get_info()
        self.page_title = ft.Text("Dashboard", size=22, weight=ft.FontWeight.W_600, color=Tema.TEXT_PRIMARY)
        self.content_area = ft.Container(expand=True, padding=24, bgcolor=Tema.BG_PRIMARY)

        self.expand = True
        self.bgcolor = Tema.BG_PRIMARY
        self.content = ft.Row(
            controls=[
                self._build_navigation(),
                ft.Container(
                    expand=True,
                    bgcolor=Tema.BG_PRIMARY,
                    content=ft.Column(
                        expand=True,
                        spacing=0,
                        controls=[self._build_header(), self.content_area],
                    ),
                ),
            ],
            spacing=0,
            expand=True,
        )
        self._render_current_view()

    def _build_navigation(self):
        nav_items = [self._nav_item(index, label, icon) for index, (label, icon, view_id) in enumerate(self.DESTINATIONS) if view_id != "empresa"]
        config_index = next(index for index, (_, _, view_id) in enumerate(self.DESTINATIONS) if view_id == "empresa")
        config_label, config_icon, _ = self.DESTINATIONS[config_index]
        return ft.Container(
            width=Tema.SIDEBAR_WIDTH,
            bgcolor=Tema.BG_SIDEBAR,
            padding=ft.Padding(12, 14, 12, 14),
            border=ft.Border(right=ft.BorderSide(1, "#24314A")),
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    self._brand(),
                    ft.Container(
                        expand=True,
                        content=ft.ListView(
                            expand=True,
                            spacing=4,
                            padding=ft.Padding(0, 6, 0, 6),
                            controls=nav_items,
                        ),
                    ),
                    self._nav_item(config_index, config_label, config_icon),
                    self._logout_button(),
                ],
            ),
        )

    def _brand(self):
        return ft.Container(
            padding=ft.Padding(8, 8, 8, 12),
            bgcolor=None,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._logo_box(56),
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(self.empresa_info.nombre, size=14, weight=ft.FontWeight.W_800, color=Tema.TEXT_ON_DARK),
                            ft.Text("Administrador", size=12, color=ft.Colors.with_opacity(0.70, Tema.TEXT_ON_DARK)),
                        ],
                    ),
                ],
            ),
        )

    def _nav_item(self, index, label, icon):
        selected = index == self.selected_index
        view_id = self.DESTINATIONS[index][2]
        is_config = view_id == "empresa"
        bg_color = "#0F1728" if selected and is_config else Tema.GOLD if selected else "#23304A" if is_config else Tema.BG_SIDEBAR
        border_color = Tema.GOLD if selected or is_config else Tema.BG_SIDEBAR
        text_color = Tema.GOLD if selected and is_config else Tema.TEXT_ON_GOLD if selected else Tema.GOLD if is_config else ft.Colors.with_opacity(0.86, Tema.TEXT_ON_DARK)
        return ft.Container(
            height=42,
            border_radius=9,
            padding=ft.Padding(12, 0, 12, 0),
            bgcolor=bg_color,
            border=ft.Border(
                left=ft.BorderSide(1, border_color),
                right=ft.BorderSide(1, border_color),
                top=ft.BorderSide(1, border_color),
                bottom=ft.BorderSide(1, border_color),
            ),
            ink=True,
            animate=180,
            animate_scale=180,
            scale=1.0,
            data={"is_config": is_config},
            on_hover=lambda event, is_selected=selected: self._nav_hover(event, is_selected),
            on_click=lambda _, idx=index: self._go_nav_index(idx),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=21, color=text_color),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_800 if selected or is_config else ft.FontWeight.W_600, color=text_color),
                ],
            ),
        )

    def _nav_hover(self, event, selected):
        if selected:
            return
        event.control.scale = 1.035 if event.data == "true" else 1.0
        is_config = bool((event.control.data or {}).get("is_config"))
        if event.data == "true":
            event.control.bgcolor = "#2B3A58" if is_config else Tema.BG_SIDEBAR_HOVER
        else:
            event.control.bgcolor = "#23304A" if is_config else Tema.BG_SIDEBAR
        try:
            event.control.update()
        except RuntimeError:
            pass

    def _logout_button(self):
        return ft.Container(
            height=42,
            border_radius=10,
            padding=ft.Padding(12, 0, 12, 0),
            bgcolor="#D92D20",
            shadow=ft.BoxShadow(blur_radius=12, color=ft.Colors.with_opacity(0.16, Tema.ERROR), offset=ft.Offset(0, 6)),
            ink=True,
            on_click=lambda _: self.on_logout(),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, color=ft.Colors.WHITE, size=20),
                    ft.Text("Cerrar sesión", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.W_800),
                ],
            ),
        )

    def _build_header(self):
        self.empresa_info = self.empresa_controller.get_info()
        return ft.Container(
            bgcolor=Tema.BG_SECONDARY,
            padding=ft.Padding(28, 16, 28, 16),
            border=ft.Border(bottom=ft.BorderSide(1, Tema.BORDER_SOFT)),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(f"{self.empresa_info.nombre} - {self.empresa_info.subtitulo}", size=22, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                            ft.Text(self.empresa_info.header_line, size=12, color=Tema.TEXT_MUTED),
                        ],
                    ),
                    self.page_title,
                ],
            ),
        )

    def _logo_box(self, size):
        if LOGO_FILE.exists():
            content = ft.Image(src=str(LOGO_FILE), width=size, height=size, fit="contain")
        else:
            content = ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=size * 0.46, color=Tema.GOLD)
        return ft.Container(
            width=size,
            height=size,
            alignment=ft.Alignment.CENTER,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=content,
        )

    def _go_nav_index(self, index):
        self.selected_index = index
        self.page_title.value = self.DESTINATIONS[self.selected_index][0]
        self._render_current_view()
        self.content = ft.Row(
            controls=[
                self._build_navigation(),
                ft.Container(
                    expand=True,
                    bgcolor=Tema.BG_PRIMARY,
                    content=ft.Column(expand=True, spacing=0, controls=[self._build_header(), self.content_area]),
                ),
            ],
            spacing=0,
            expand=True,
        )
        self.update()

    def _render_current_view(self):
        view_id = self.DESTINATIONS[self.selected_index][2]
        if view_id == "dashboard":
            self._render_dashboard()
            return
        self.content_area.content = self.VIEW_FACTORY[view_id]()

    def _render_dashboard(self):
        try:
            db = SessionLocal()
            try:
                catalog = CatalogController(db).dashboard_counts()
                inventory = InventoryController(db).inventory_summary()
                sales_ctrl = SalesController(db)
                sales = sales_ctrl.order_counts()
                daily_sales = sales_ctrl.daily_sales_total()
                low_stock = InventoryController(db).low_stock_variants()[:6]
                chart_data = self._dashboard_chart_data(db)
            finally:
                db.close()
        except Exception as exc:
            self.content_area.content = self._panel([
                ft.Text("No se pudo cargar el dashboard", color=Tema.ERROR, weight=ft.FontWeight.W_700),
                ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12, selectable=True),
            ])
            return

        self.content_area.content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                self._dashboard_hero(daily_sales, inventory, sales),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=[
                    self._metric_card("Ventas del día", f"${float(daily_sales):,.0f}", ft.Icons.POINT_OF_SALE_ROUNDED, Tema.SUCCESS, 3),
                    self._metric_card("Productos activos", str(catalog["productos"]), ft.Icons.CATEGORY_ROUNDED, Tema.GOLD, 3),
                    self._metric_card("Variantes SKU", str(catalog["variantes"]), ft.Icons.QR_CODE_2_ROUNDED, Tema.INFO, 3),
                    self._metric_card("Stock bajo", str(inventory["stock_bajo"]), ft.Icons.WARNING_AMBER_ROUNDED, Tema.WARNING, 3),
                    self._metric_card("Agotados", str(inventory["agotados"]), ft.Icons.REMOVE_CIRCLE_OUTLINE_ROUNDED, Tema.ERROR, 3),
                    self._metric_card("Valor inventario", f"${inventory['valor_inventario']:,.0f}", ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, Tema.SUCCESS, 3),
                    self._metric_card("Pedidos pendientes", str(sales["pendientes"]), ft.Icons.HOURGLASS_EMPTY_ROUNDED, Tema.WARNING, 3),
                    self._metric_card("En preparación", str(sales["preparacion"]), ft.Icons.PENDING_ACTIONS_ROUNDED, Tema.INFO, 3),
                ]),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=[
                    ft.Container(col={"xs": 12, "lg": 4}, content=self._bar_chart_panel("Ventas últimos 7 días", chart_data["ventas"], Tema.SUCCESS, money=True)),
                    ft.Container(col={"xs": 12, "lg": 4}, content=self._bar_chart_panel("Usuarios registrados", chart_data["usuarios"], Tema.INFO)),
                    ft.Container(col={"xs": 12, "lg": 4}, content=self._status_mix_panel("Pedidos por estado", chart_data["pedidos"])),
                ]),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=[
                    ft.Container(col={"xs": 12, "md": 7}, content=self._low_stock_panel(low_stock)),
                    ft.Container(col={"xs": 12, "md": 5}, content=self._corporate_panel(inventory["stock_total"])),
                ]),
            ],
        )

    def _dashboard_chart_data(self, db):
        sales_rows = db.execute(text("""
            SELECT TO_CHAR(day::date, 'DD/MM') AS label, COALESCE(SUM(p.total), 0) AS value
            FROM generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, INTERVAL '1 day') AS day
            LEFT JOIN pedidos p ON DATE(p.fecha_pedido) = day::date
            GROUP BY day
            ORDER BY day
        """)).mappings().all()
        user_rows = db.execute(text("""
            SELECT TO_CHAR(month::date, 'MM/YYYY') AS label, COALESCE(COUNT(u.id_usuario), 0) AS value
            FROM generate_series(date_trunc('month', CURRENT_DATE) - INTERVAL '5 months', date_trunc('month', CURRENT_DATE), INTERVAL '1 month') AS month
            LEFT JOIN usuarios u ON date_trunc('month', u.fecha_registro) = month
            GROUP BY month
            ORDER BY month
        """)).mappings().all()
        order_rows = db.execute(text("""
            SELECT ep.descripcion_estado AS label, COUNT(p.id_pedido) AS value
            FROM estado_pedido ep
            LEFT JOIN pedidos p ON p.id_estado_pedido = ep.id_estado_pedido
            GROUP BY ep.descripcion_estado
            ORDER BY value DESC, ep.descripcion_estado ASC
            LIMIT 6
        """)).mappings().all()
        return {
            "ventas": [(row["label"], float(row["value"] or 0)) for row in sales_rows],
            "usuarios": [(row["label"], int(row["value"] or 0)) for row in user_rows],
            "pedidos": [(row["label"], int(row["value"] or 0)) for row in order_rows],
        }

    def _dashboard_hero(self, daily_sales, inventory, sales):
        return ft.Container(
            bgcolor=Tema.BG_SIDEBAR,
            border_radius=16,
            padding=24,
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.18, "#172033"), offset=ft.Offset(0, 12)),
            content=ft.ResponsiveRow(
                spacing=18,
                run_spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(col={"xs": 12, "lg": 5}, content=ft.Column(spacing=8, controls=[
                        ft.Text("Resumen administrativo", size=13, weight=ft.FontWeight.W_700, color=Tema.GOLD),
                        ft.Text("Sueños Dorados", size=30, weight=ft.FontWeight.W_800, color=Tema.TEXT_ON_DARK),
                        ft.Text("Ventas, inventario y pedidos conectados en tiempo real.", size=13, color=ft.Colors.with_opacity(0.78, Tema.TEXT_ON_DARK)),
                    ])),
                    ft.Container(col={"xs": 12, "sm": 4, "lg": 2}, content=self._hero_stat("Ventas hoy", f"${float(daily_sales):,.0f}", Tema.SUCCESS)),
                    ft.Container(col={"xs": 12, "sm": 4, "lg": 2}, content=self._hero_stat("Inventario", str(inventory["stock_total"]), Tema.GOLD)),
                    ft.Container(col={"xs": 12, "sm": 4, "lg": 3}, content=self._hero_stat("Pendientes", str(sales["pendientes"]), Tema.WARNING)),
                ],
            ),
        )

    def _hero_stat(self, title, value, color):
        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
            border_radius=12,
            padding=16,
            border=ft.Border(left=ft.BorderSide(3, color)),
            content=ft.Column(spacing=5, controls=[
                ft.Text(title, size=12, color=ft.Colors.with_opacity(0.72, Tema.TEXT_ON_DARK)),
                ft.Text(value, size=23, weight=ft.FontWeight.W_800, color=Tema.TEXT_ON_DARK),
            ]),
        )

    def _metric_card(self, title, value, icon, color, col):
        return ft.Container(
            col={"xs": 12, "sm": 6, "lg": col},
            bgcolor=Tema.BG_CARD,
            border_radius=14,
            padding=18,
            border=ft.Border(left=ft.BorderSide(4, color), right=ft.BorderSide(1, Tema.BORDER_SOFT), top=ft.BorderSide(1, Tema.BORDER_SOFT), bottom=ft.BorderSide(1, Tema.BORDER_SOFT)),
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.08, "#172033"), offset=ft.Offset(0, 8)),
            content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Column(spacing=6, controls=[ft.Text(title, size=12, color=Tema.TEXT_MUTED), ft.Text(value, size=24, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY)]),
                ft.Container(content=ft.Icon(icon, color=color, size=24), width=46, height=46, alignment=ft.Alignment.CENTER, bgcolor=ft.Colors.with_opacity(0.12, color), border_radius=10),
            ]),
        )

    def _bar_chart_panel(self, title, data, color, money=False):
        max_value = max([value for _, value in data], default=0) or 1
        bars = []
        for label, value in data:
            height = max(8, int((float(value) / float(max_value)) * 120))
            value_text = f"${value:,.0f}" if money else str(int(value))
            bars.append(ft.Container(expand=True, content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
                spacing=6,
                controls=[
                    ft.Text(value_text, size=10, color=Tema.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Container(width=26, height=height, border_radius=6, bgcolor=color),
                    ft.Text(self._short_chart_label(label), size=10, color=Tema.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER, tooltip=str(label)),
                ],
            )))
        if not bars:
            bars = [ft.Text("Sin datos para graficar", color=Tema.TEXT_MUTED, size=12)]
        return self._panel([
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY), ft.Icon(ft.Icons.INSIGHTS_ROUNDED, color=color)]),
            ft.Container(height=172, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END, spacing=8, controls=bars)),
        ])

    def _status_mix_panel(self, title, data):
        total = sum(value for _, value in data) or 1
        colors = [Tema.GOLD, Tema.INFO, Tema.SUCCESS, Tema.WARNING, Tema.ERROR, "#6B7280"]
        rows = []
        for index, (label, value) in enumerate(data):
            pct = int((value / total) * 100) if total else 0
            color = colors[index % len(colors)]
            rows.append(ft.Column(spacing=5, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(self._short_chart_label(label), size=12, color=Tema.TEXT_SECONDARY, weight=ft.FontWeight.W_700),
                    ft.Text(f"{int(value)} ({pct}%)", size=12, color=Tema.TEXT_MUTED),
                ]),
                ft.Container(height=9, bgcolor="#EEF2F6", border_radius=20, content=ft.Row(controls=[ft.Container(width=max(12, pct * 2.2), height=9, bgcolor=color, border_radius=20)])),
            ]))
        if not rows:
            rows = [ft.Text("Sin datos para graficar", color=Tema.TEXT_MUTED, size=12)]
        return self._panel([
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY), ft.Icon(ft.Icons.DONUT_LARGE_ROUNDED, color=Tema.GOLD)]),
            ft.Column(spacing=12, controls=rows),
        ])

    def _short_chart_label(self, label):
        replacements = {"Despachado": "Desp.", "En preparación": "Prep.", "Pendiente": "Pend.", "Cancelado": "Canc.", "Entregado": "Entr."}
        return replacements.get(str(label), str(label))

    def _low_stock_panel(self, variants):
        controls = [ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Alertas de stock", size=16, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY), ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=Tema.WARNING)])]
        if not variants:
            controls.append(ft.Text("Sin alertas activas", color=Tema.TEXT_MUTED))
        for variant in variants:
            controls.append(ft.Container(
                padding=ft.Padding(0, 10, 0, 10),
                border=ft.Border(bottom=ft.BorderSide(1, Tema.BORDER)),
                content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Column(spacing=2, controls=[ft.Text(variant.sku, color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.W_600), ft.Text(f"{variant.producto.nombre_producto} | {variant.referencia}", color=Tema.TEXT_MUTED, size=12)]),
                    self._badge("Agotado" if variant.stock <= 0 else f"{variant.stock} uds", Tema.ERROR if variant.stock <= 0 else Tema.WARNING),
                ]),
            ))
        return self._panel(controls)

    def _corporate_panel(self, stock_total):
        return self._panel([
            ft.Text("Control operativo", size=16, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY),
            ft.Text("Inventario físico en tiempo real", size=12, color=Tema.TEXT_MUTED),
            ft.Divider(color=Tema.BORDER),
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=Tema.SUCCESS), ft.Text("Stock total disponible", color=Tema.TEXT_SECONDARY), ft.Text(str(stock_total), color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Icon(ft.Icons.LOCK_ROUNDED, color=Tema.INFO), ft.Text("Descuento atómico al aprobar pago", color=Tema.TEXT_SECONDARY)]),
            ft.Row([ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, color=Tema.ERROR), ft.Text("Factura PDF preparada con ReportLab", color=Tema.TEXT_SECONDARY)]),
            ft.Row([ft.Icon(ft.Icons.LOCAL_SHIPPING_ROUNDED, color=Tema.GOLD), ft.Text("Guías y transportadora por pedido", color=Tema.TEXT_SECONDARY)]),
        ])

    def _panel(self, controls):
        return ft.Container(
            bgcolor=Tema.BG_CARD,
            border_radius=10,
            padding=18,
            border=ft.Border(left=ft.BorderSide(1, Tema.BORDER_SOFT), right=ft.BorderSide(1, Tema.BORDER_SOFT), top=ft.BorderSide(1, Tema.BORDER_SOFT), bottom=ft.BorderSide(1, Tema.BORDER_SOFT)),
            shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK), offset=ft.Offset(0, 7)),
            content=ft.Column(spacing=10, controls=controls),
        )

    def _badge(self, text_value, color):
        return ft.Container(bgcolor=color, border_radius=6, padding=ft.Padding(8, 3, 8, 3), content=ft.Text(text_value, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.W_600))

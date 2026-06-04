from decimal import Decimal
import re
import shutil
from pathlib import Path
from datetime import date, datetime
from uuid import uuid4

import flet as ft
from sqlalchemy import text

from config import BASE_DIR
from database import SessionLocal
from utils.theme import Tema
from views.crud_metadata import LOOKUP_CONFIG

COLOR_PALETTE = [
    ("Negro", "#111827"),
    ("Blanco", "#FFFFFF"),
    ("Dorado", "#E7A21B"),
    ("Rojo", "#D92D20"),
    ("Verde", "#1F9D55"),
    ("Azul", "#2563EB"),
    ("Morado", "#7C3AED"),
    ("Rosa", "#DB2777"),
    ("Gris", "#6B7280"),
    ("Café", "#92400E"),
]

IMAGE_UPLOAD_DIR = BASE_DIR / "imagenes_app" / "productos"

class BaseCrudView(ft.Container):
    def __init__(self, group_id, group_config, display_queries=None):
        super().__init__()
        self.crud_groups = {group_id: group_config}
        self.display_queries = display_queries or {}
        self.on_logout = None
        self.selected_index = 0
        self.current_group_id = None
        self.current_config = None
        self.selected_record_id = None
        self.selected_record_text = ft.Text("Registro seleccionado: ninguno", size=12, color=Tema.TEXT_MUTED)
        self.feedback_banner = ft.Container(visible=False)
        self.form_controls = {}
        self.table_selector = None
        self.search_field = None
        self.order_field = None
        self.row_stock_fields = {}
        self.stock_variant_selector = None
        self.stock_delta_field = ft.TextField(
            label="Unidades",
            hint_text="Ej: 5",
            width=132,
            dense=True,
            prefix_icon=ft.Icons.NUMBERS_ROUNDED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor=Tema.BG_INPUT,
            color=Tema.TEXT_PRIMARY,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self.crud_area = ft.Container(expand=True)
        self.page_title = ft.Text(self.crud_groups[group_id]["title"], size=22, weight=ft.FontWeight.W_600, color=Tema.TEXT_PRIMARY)
        self.content_area = ft.Container(expand=True, bgcolor=Tema.BG_PRIMARY)

        self.expand = True
        self.bgcolor = Tema.BG_PRIMARY
        self.content = self.content_area
        self._render_crud_group(group_id)

    def _render_crud_group(self, group_id):
        self.current_group_id = group_id
        group = self.crud_groups[group_id]
        self.table_selector = ft.Dropdown(width=260, label="Tabla", editable=True, enable_filter=True, enable_search=True, menu_height=300, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor=Tema.BG_INPUT, color=Tema.TEXT_PRIMARY, options=[ft.dropdown.Option(t["label"]) for t in group["tables"]], value=group["tables"][0]["label"], on_select=lambda _: self._select_crud_table())
        self.search_field = ft.TextField(label="Buscar", width=260, dense=True, prefix_icon=ft.Icons.SEARCH_ROUNDED, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor=Tema.BG_INPUT, color=Tema.TEXT_PRIMARY, on_submit=lambda _: self._refresh_crud_table())
        self.order_field = ft.Dropdown(width=220, label="Ordenar por", editable=True, enable_filter=True, enable_search=True, menu_height=300, border_color=Tema.BORDER, focused_border_color=Tema.GOLD, bgcolor=Tema.BG_INPUT, color=Tema.TEXT_PRIMARY, options=[], on_select=lambda _: self._refresh_crud_table())
        self.content_area.content = ft.Column(expand=True, spacing=16, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Column(spacing=3, controls=[ft.Text(group["title"], size=18, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY), ft.Text("Gestiona registros, movimientos y consultas conectadas a PostgreSQL.", size=12, color=Tema.TEXT_MUTED)]),
                ft.Row([self.search_field, ft.IconButton(icon=ft.Icons.SEARCH_ROUNDED, tooltip="Buscar", on_click=lambda _: self._refresh_crud_table()), self.order_field, self.table_selector], spacing=12, wrap=True),
            ]),
            self.crud_area,
        ])
        self._select_crud_table()

    def _select_crud_table(self):
        self._clear_feedback()
        group = self.crud_groups[self.current_group_id]
        self.current_config = next(t for t in group["tables"] if t["label"] == self.table_selector.value)
        self.selected_record_id = None
        columns = [self.current_config["pk"]] + [name for name, _ in self.current_config["fields"]]
        self.order_field.options = [ft.dropdown.Option(column) for column in columns]
        self.order_field.value = self.current_config["pk"]
        if self.search_field:
            self.search_field.value = ""
        self._build_crud_content()

    def _build_field_control(self, field_name, field_type):
        if field_type == "bool":
            return ft.Dropdown(
                label=self._pretty(field_name),
                width=390,
                dense=True,
                border_color=Tema.BORDER,
                focused_border_color=Tema.GOLD,
                bgcolor="#FFFFFF",
                color=Tema.TEXT_PRIMARY,
                options=[
                    ft.dropdown.Option(key="true", text="Activo"),
                    ft.dropdown.Option(key="false", text="Inactivo"),
                ],
                value="true",
                hint_text="Elige el estado",
            )
        if field_type == "date":
            control = ft.TextField(
                label=self._pretty(field_name),
                hint_text="Selecciona una fecha",
                width=390,
                dense=True,
                read_only=True,
                prefix_icon=ft.Icons.CALENDAR_MONTH_ROUNDED,
                suffix_icon=ft.Icons.EVENT_AVAILABLE_ROUNDED,
                border_color=Tema.BORDER,
                focused_border_color=Tema.GOLD,
                bgcolor="#FFFFFF",
                color=Tema.TEXT_PRIMARY,
                always_call_on_tap=True,
            )
            control.on_click = lambda _, target=control: self._open_date_picker(target)
            return control
        if field_name == "codigo_hex":
            return self._build_color_palette_control(field_name)
        if field_name == "url_imagen":
            return self._build_image_picker_control(field_name)
        if field_name in LOOKUP_CONFIG:
            return ft.Dropdown(
                label=self._pretty(field_name),
                width=390,
                dense=True,
                editable=True,
                enable_filter=True,
                enable_search=True,
                menu_height=210,
                menu_width=430,
                border_color=Tema.BORDER,
                focused_border_color=Tema.GOLD,
                bgcolor="#FFFFFF",
                color=Tema.TEXT_PRIMARY,
                options=self._lookup_options(field_name),
                hint_text="Busca y selecciona",
            )
        return ft.TextField(
            label=self._pretty(field_name),
            width=390,
            dense=True,
            password=(field_type == "password"),
            can_reveal_password=(field_type == "password"),
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
        )

    def _build_color_palette_control(self, field_name):
        field = ft.TextField(
            label=self._pretty(field_name),
            hint_text="#RRGGBB",
            width=390,
            dense=True,
            prefix_icon=ft.Icons.PALETTE_ROUNDED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
        )

        def select_color(hex_value):
            field.value = hex_value
            try:
                field.update()
            except RuntimeError:
                pass

        swatches = [
            ft.Container(
                width=28,
                height=28,
                border_radius=6,
                bgcolor=hex_value,
                border=ft.Border(
                    left=ft.BorderSide(1, Tema.BORDER),
                    right=ft.BorderSide(1, Tema.BORDER),
                    top=ft.BorderSide(1, Tema.BORDER),
                    bottom=ft.BorderSide(1, Tema.BORDER),
                ),
                tooltip=f"{name} {hex_value}",
                ink=True,
                on_click=lambda _, color=hex_value: select_color(color),
            )
            for name, hex_value in COLOR_PALETTE
        ]
        return field, ft.Column(spacing=8, controls=[field, ft.Row(spacing=7, wrap=True, controls=swatches)])

    def _build_image_picker_control(self, field_name):
        field = ft.TextField(
            label=self._pretty(field_name),
            hint_text="URL o ruta de imagen",
            width=650,
            dense=True,
            prefix_icon=ft.Icons.IMAGE_ROUNDED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
        )
        async def open_picker(_):
            await self._open_image_file_picker(field)

        button = ft.OutlinedButton(
            "Buscar archivo",
            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
            on_click=open_picker,
            style=ft.ButtonStyle(
                color="#B35A00",
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#F0A23A")},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(14, 10, 14, 10),
            ),
        )
        return field, ft.Row(spacing=10, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[field, button])

    def _lookup_options(self, field_name):
        cfg = LOOKUP_CONFIG[field_name]
        sql = cfg.get("select")
        if not sql:
            select_columns = [cfg["pk"], *cfg["columns"]]
            sql = f"SELECT {', '.join(select_columns)} FROM {cfg['table']} ORDER BY {cfg['pk']} DESC"
        required_color = field_name == "id_color" and self.current_config and self.current_config.get("table") == "variantes_producto"
        options = [] if required_color else [ft.dropdown.Option(key="", text="Sin seleccionar")]
        try:
            db = SessionLocal()
            try:
                rows = db.execute(text(sql)).mappings().all()
            finally:
                db.close()
        except Exception:
            return options
        for row in rows:
            details = " - ".join(str(row[column]) for column in cfg["columns"] if row.get(column) not in (None, ""))
            label = details or str(row[cfg["pk"]])
            options.append(ft.dropdown.Option(key=str(row[cfg["pk"]]), text=label))
        return options

    def _open_date_picker(self, target):
        today = date.today()
        selected_date = today
        if target.value:
            try:
                selected_date = max(date.fromisoformat(str(target.value).strip()), today)
            except ValueError:
                selected_date = today

        def on_change(event):
            if event.control.value:
                value = event.control.value
                target.value = (value.date() if hasattr(value, "date") else value).isoformat()
                target.update()

        picker_args = {
            "first_date": datetime.combine(today, datetime.min.time()),
            "last_date": datetime(today.year + 10, 12, 31),
            "value": datetime.combine(selected_date, datetime.min.time()),
            "on_change": on_change,
        }
        try:
            picker = ft.DatePicker(
                **picker_args,
                bgcolor="#FFFFFF",
                header_bgcolor=Tema.BG_SIDEBAR,
                header_foreground_color="#FFFFFF",
                selected_day_bgcolor=Tema.BG_SIDEBAR,
                selected_day_color="#FFFFFF",
                today_border_color=Tema.GOLD,
            )
        except TypeError:
            picker = ft.DatePicker(**picker_args)
        self._apply_date_picker_theme()
        try:
            self.page.open(picker)
        except Exception:
            if picker not in self.page.overlay:
                self.page.overlay.append(picker)
            picker.open = True
            self.page.update()

    def _apply_date_picker_theme(self):
        try:
            if self.page.theme is None:
                self.page.theme = ft.Theme()
            self.page.theme.date_picker_theme = ft.DatePickerTheme(
                bgcolor="#FFFFFF",
                header_bgcolor=Tema.BG_SIDEBAR,
                header_foreground_color="#FFFFFF",
                day_foreground_color={
                    ft.ControlState.SELECTED: "#FFFFFF",
                    ft.ControlState.DEFAULT: Tema.TEXT_PRIMARY,
                },
                day_bgcolor={
                    ft.ControlState.SELECTED: Tema.BG_SIDEBAR,
                    ft.ControlState.HOVERED: "#EEF3FB",
                },
                today_foreground_color=Tema.BG_SIDEBAR,
                today_bgcolor="#FFFFFF",
                today_border_side=ft.BorderSide(1, Tema.GOLD),
            )
            self.page.update()
        except Exception:
            pass

    async def _open_image_file_picker(self, target):
        picker = ft.FilePicker()
        if hasattr(self.page, "services"):
            if picker not in self.page.services:
                self.page.services.append(picker)
        elif picker not in self.page.overlay:
            self.page.overlay.append(picker)
        self.page.update()
        try:
            file_type = getattr(ft.FilePickerFileType, "CUSTOM", None)
            files = await picker.pick_files(
                allow_multiple=False,
                file_type=file_type,
                allowed_extensions=["png", "jpg", "jpeg", "webp", "gif"],
            )
        except TypeError:
            files = await picker.pick_files(allow_multiple=False)

        if not files:
            return
        try:
            target.value = self._store_image_file(files[0].path)
            target.update()
        except Exception as exc:
            self._show_dialog_error(f"No se pudo cargar la imagen: {exc}")

    def _store_image_file(self, source_path):
        if not source_path:
            raise ValueError("No se pudo leer la ruta del archivo seleccionado")
        source = Path(source_path)
        if not source.exists():
            raise ValueError("El archivo seleccionado no existe")
        IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", source.stem).strip("-") or "imagen"
        destination = IMAGE_UPLOAD_DIR / f"{safe_stem}-{uuid4().hex[:8]}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        return str(destination.relative_to(BASE_DIR)).replace("\\", "/")

    def _build_crud_content(self):
        config = self.current_config
        actions = [
            self._primary_button(f"Nuevo {config['label']}", ft.Icons.ADD_ROUNDED, lambda _: self._open_record_dialog()),
        ]
        if config["table"] == "variantes_producto":
            actions.extend([
                self._outline_button("Exportar Excel", ft.Icons.DOWNLOAD_ROUNDED, lambda _: self._export_inventory_excel()),
            ])
        actions.append(ft.IconButton(icon=ft.Icons.REFRESH_ROUNDED, tooltip="Refrescar", on_click=lambda _: self._refresh_crud_table()))
        content_controls = [
            self.feedback_banner,
            self._panel([
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text(config["label"], size=16, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
                            ft.Text("Edita desde la tabla o crea un registro en una ventana flotante.", size=12, color=Tema.TEXT_MUTED),
                        ]),
                        ft.Row(actions, spacing=8, wrap=True),
                    ],
                ),
                self.selected_record_text,
            ]),
        ]
        if config["table"] == "variantes_producto":
            content_controls.append(self._stock_adjust_panel())
        table_content = self._load_crud_table()

        self.crud_area.content = ft.Column(
            expand=True,
            spacing=14,
            controls=[
                *content_controls,
                ft.Container(expand=True, content=table_content),
            ],
        )
        try:
            self.crud_area.update()
        except RuntimeError:
            pass

    def _build_form_rows(self):
        self.form_controls = {}
        rows = []
        for field_name, field_type in self.current_config["fields"]:
            built_control = self._build_field_control(field_name, field_type)
            if isinstance(built_control, tuple):
                control, display_control = built_control
            else:
                control = display_control = built_control
            self.form_controls[field_name] = control
            rows.append(ft.Container(col={"xs": 12, "md": 6}, content=display_control))
        controls = [
            ft.ResponsiveRow(spacing=12, run_spacing=12, controls=rows),
        ]
        if self.current_config["table"] == "usuarios":
            controls.extend(self._build_user_address_fields())
        return controls

    def _open_record_dialog(self, record=None):
        self.selected_record_id = None if record is None else record[self.current_config["pk"]]
        title = f"Nuevo {self.current_config['label']}" if record is None else f"Editar {self.current_config['label']}"
        form_controls = self._build_form_rows()
        if record is None:
            self.selected_record_text.value = "Registro seleccionado: nuevo"
        else:
            self._fill_form_from_record(record)
        form_height = 470 if len(self.current_config["fields"]) > 6 or self.current_config["table"] == "usuarios" else 330
        self.dialog_feedback = ft.Container(visible=False)
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            elevation=18,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=None,
            content_padding=0,
            actions_padding=ft.Padding(22, 12, 22, 18),
            content=ft.Container(
                width=860,
                height=form_height,
                bgcolor="#FFFFFF",
                border_radius=16,
                content=ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(24, 18, 18, 14),
                            bgcolor=Tema.BG_SIDEBAR,
                            border_radius=ft.BorderRadius(16, 16, 0, 0),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(spacing=12, controls=[
                                        ft.Container(width=42, height=42, border_radius=10, bgcolor=Tema.GOLD, alignment=ft.Alignment.CENTER, content=ft.Icon(ft.Icons.EDIT_DOCUMENT, color=Tema.TEXT_ON_GOLD, size=22)),
                                        ft.Column(spacing=2, controls=[
                                            ft.Text(title, size=18, weight=ft.FontWeight.W_800, color=Tema.TEXT_ON_DARK),
                                            ft.Text("Campos organizados para guardar rápido y sin perder contexto.", size=12, color=ft.Colors.with_opacity(0.78, Tema.TEXT_ON_DARK)),
                                        ]),
                                    ]),
                                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, icon_color=Tema.TEXT_ON_DARK, tooltip="Cerrar", on_click=lambda _: self._close_dialog(dialog)),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=ft.Padding(24, 18, 24, 12),
                            content=ft.Column(
                                expand=True,
                                scroll=ft.ScrollMode.AUTO,
                                spacing=14,
                                controls=[
                                    ft.Container(
                                        bgcolor=Tema.GOLD_SOFT,
                                        border_radius=8,
                                        padding=ft.Padding(12, 9, 12, 9),
                                        border=ft.Border(left=ft.BorderSide(3, Tema.GOLD)),
                                        content=ft.Row(spacing=8, controls=[
                                            ft.Icon(ft.Icons.SEARCH_ROUNDED, color=Tema.GOLD_DARK, size=18),
                                            ft.Text("En los desplegables puedes escribir para buscar.", size=12, color=Tema.TEXT_SECONDARY),
                                        ]),
                                    ),
                                    self.dialog_feedback,
                                    *form_controls,
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                self._primary_button("Guardar", ft.Icons.SAVE_ROUNDED, lambda _: self._save_record(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page = self.page
        dialog.open = True
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        page.update()

    def _fill_form_from_record(self, record):
        self.selected_record_text.value = f"Registro seleccionado: {self.current_config['label']}"
        for field_name, field_type in self.current_config["fields"]:
            control = self.form_controls[field_name]
            value = record.get(field_name)
            if field_type == "bool":
                control.value = "true" if bool(value) else "false"
            elif field_type == "password":
                control.value = ""
                control.hint_text = "Dejar vacío para conservar contraseña"
            else:
                control.value = "" if value is None else str(value)
        if self.current_config["table"] == "usuarios":
            address_map = {
                "direccion_descripcion": "descripcion_direccion",
                "direccion_barrio": "descripcion_barrio",
                "direccion_municipio": "descripcion_municipio",
                "direccion_departamento": "descripcion_departamento",
            }
            for control_name, record_name in address_map.items():
                if control_name in self.form_controls:
                    self.form_controls[control_name].value = "" if record.get(record_name) is None else str(record.get(record_name))
            if "direccion_principal" in self.form_controls:
                self.form_controls["direccion_principal"].value = bool(record.get("es_principal", True))

    def _primary_button(self, text_value, icon, on_click):
        return ft.FilledButton(
            text_value,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: "#F4A51C", ft.ControlState.HOVERED: "#E88908"},
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(18, 12, 18, 12),
            ),
        )

    def _outline_button(self, text_value, icon, on_click):
        return ft.OutlinedButton(
            text_value,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color="#B35A00",
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#F0A23A")},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(16, 11, 16, 11),
            ),
        )

    def _load_crud_table(self):
        config = self.current_config
        if config["table"] == "usuarios":
            return self._load_users_table(config)
        if config["table"] == "direcciones":
            return self._load_addresses_table(config)
        if config["table"] == "descuentos":
            return self._load_discounts_table(config)
        if config["table"] == "variantes_producto":
            return self._load_variants_stock_table(config)
        if config["table"] in self.display_queries:
            return self._load_display_table(config)
        columns = [config["pk"]] + [name for name, _ in config["fields"]]
        order_col = self.order_field.value if self.order_field and self.order_field.value in columns else config["pk"]
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = " WHERE " + " OR ".join(f"CAST({col} AS TEXT) ILIKE :search" for col in columns)
            params["search"] = f"%{search_value}%"
        sql = f"SELECT {', '.join(columns)} FROM {config['table']}{where_sql} ORDER BY {order_col} DESC LIMIT 35"
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar esta tabla", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        rows = []
        display_columns = [col for col in columns if col != config["pk"] and not col.startswith("id_")]
        for item in rows_data:
            record = dict(item)
            rows.append(ft.DataRow(cells=[self._action_cell(record)] + [self._text_cell(record.get(col)) for col in display_columns]))
        return self._table_panel(f"{len(rows_data)} registros", ["Acciones"] + [self._pretty(c) for c in display_columns], rows)

    def _load_display_table(self, config):
        spec = self.display_queries[config["table"]]
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
            return self._panel([ft.Text("No se pudo cargar esta tabla", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        if config["table"] == "imagenes_producto":
            return self._image_cards_panel(rows_data)
        rows = []
        for item in rows_data:
            record = dict(item)
            rows.append(ft.DataRow(cells=[self._action_cell(record)] + [self._display_cell(record.get(col), col) for col in spec["columns"]]))
        return self._table_panel(f"{len(rows_data)} registros", ["Acciones"] + spec["headings"], rows)

    def _image_cards_panel(self, rows_data):
        records = [dict(item) for item in rows_data]
        if not records:
            return self._panel([
                ft.Text("0 imágenes", size=14, color=Tema.TEXT_MUTED, weight=ft.FontWeight.W_700),
                ft.Text("Aún no hay imágenes registradas.", color=Tema.TEXT_MUTED, size=12),
            ])
        cards = [ft.Container(col={"xs": 12, "sm": 6, "lg": 4, "xl": 3}, content=self._image_card(record)) for record in records]
        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{len(records)} imágenes", size=14, color=Tema.TEXT_MUTED, weight=ft.FontWeight.W_700),
                        ft.Container(
                            border_radius=20,
                            bgcolor=Tema.GOLD_SOFT,
                            padding=ft.Padding(10, 4, 10, 4),
                            content=ft.Text("Galería visual", size=11, color=Tema.GOLD_DARK, weight=ft.FontWeight.W_700),
                        ),
                    ],
                ),
                ft.ResponsiveRow(spacing=16, run_spacing=16, controls=cards),
            ],
        )

    def _image_card(self, record):
        image_src = self._image_src(record.get("url_imagen"))
        estado = "Activo" if record.get("es_principal") else "Inactivo"
        estado_color = Tema.SUCCESS if record.get("es_principal") else Tema.ERROR
        return ft.Container(
            bgcolor=Tema.BG_CARD,
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.Border(
                left=ft.BorderSide(1, Tema.BORDER_SOFT),
                right=ft.BorderSide(1, Tema.BORDER_SOFT),
                top=ft.BorderSide(1, Tema.BORDER_SOFT),
                bottom=ft.BorderSide(1, Tema.BORDER_SOFT),
            ),
            shadow=ft.BoxShadow(blur_radius=22, color=ft.Colors.with_opacity(0.08, "#172033"), offset=ft.Offset(0, 9)),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=238,
                        bgcolor=Tema.BG_TABLE_HEAD,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Image(src=image_src, fit="cover", width=999, height=238) if image_src else ft.Icon(ft.Icons.BROKEN_IMAGE_ROUNDED, color=Tema.TEXT_MUTED, size=46),
                    ),
                    ft.Container(
                        padding=ft.Padding(12, 9, 12, 10),
                        content=ft.Column(
                            spacing=6,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(record.get("producto") or "Producto sin nombre", size=13, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                                        ft.Container(border_radius=20, bgcolor=ft.Colors.with_opacity(0.10, estado_color), padding=ft.Padding(7, 2, 7, 2), content=ft.Text(estado, size=9, weight=ft.FontWeight.W_800, color=estado_color)),
                                    ],
                                ),
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Text(f"Color: {record.get('color') or 'Sin color'}", size=11, color=Tema.TEXT_SECONDARY, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(f"Orden: {record.get('orden')}", size=11, color=Tema.TEXT_MUTED),
                                    ],
                                ),
                                ft.Text(str(record.get("url_imagen") or "Sin ruta"), size=10, color=Tema.TEXT_MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, selectable=True),
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Row(
                                            spacing=4,
                                            controls=[
                                                ft.IconButton(icon=ft.Icons.EDIT_ROUNDED, icon_color=Tema.GOLD, tooltip="Editar", width=34, height=34, icon_size=18, on_click=lambda _, rec=record: self._edit_record(rec)),
                                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE_ROUNDED, icon_color=Tema.ERROR, tooltip="Eliminar", width=34, height=34, icon_size=18, on_click=lambda _, rec=record: self._confirm_delete(rec)),
                                            ],
                                        ),
                                        self._boolean_switch(record, "es_principal"),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _image_src(self, value):
        if not value:
            return None
        text_value = str(value)
        if text_value.startswith(("http://", "https://")):
            return text_value
        image_path = Path(text_value)
        if not image_path.is_absolute():
            image_path = BASE_DIR / image_path
        return str(image_path)

    def _action_cell(self, record):
        bool_field = self._boolean_field()
        actions = [
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
        ]
        if bool_field and bool_field in record:
            actions.append(self._boolean_switch(record, bool_field))
        return ft.DataCell(
            ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=actions,
            )
        )

    def _boolean_field(self):
        if not self.current_config:
            return None
        bool_fields = [name for name, field_type in self.current_config["fields"] if field_type == "bool"]
        return bool_fields[-1] if bool_fields else None

    def _boolean_switch(self, record, field_name):
        current_value = bool(record.get(field_name))
        return ft.Container(
            width=42,
            height=28,
            alignment=ft.Alignment.CENTER,
            content=ft.Switch(
                value=current_value,
                active_color=Tema.SUCCESS,
                inactive_thumb_color=Tema.ERROR,
                scale=0.72,
                tooltip="Activar / desactivar",
                on_change=lambda event, rec=record, field=field_name, previous=current_value: self._confirm_boolean_toggle(rec, field, event.control.value, previous),
            ),
        )

    def _confirm_boolean_toggle(self, record, field_name, new_value, previous_value):
        record_id = record.get(self.current_config["pk"])
        action = "activar" if new_value else "desactivar"
        label = self._record_title(record)
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            elevation=18,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.TASK_ALT_ROUNDED if new_value else ft.Icons.BLOCK_ROUNDED, color=Tema.SUCCESS if new_value else Tema.ERROR),
                            ft.Text(f"Confirmar {action}", color=Tema.TEXT_PRIMARY, weight=ft.FontWeight.W_800),
                        ],
                    ),
                    ft.IconButton(icon=ft.Icons.CLOSE_ROUNDED, tooltip="Cerrar", on_click=lambda _: self._cancel_boolean_toggle(dialog)),
                ],
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(f"¿Seguro que quieres {action} este registro?", size=13, color=Tema.TEXT_SECONDARY),
                        ft.Container(
                            bgcolor="#F8FAFC",
                            border_radius=8,
                            padding=ft.Padding(12, 10, 12, 10),
                            border=ft.Border(left=ft.BorderSide(3, Tema.SUCCESS if new_value else Tema.ERROR)),
                            content=ft.Text(label, size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY, selectable=True),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._cancel_boolean_toggle(dialog)),
                ft.FilledButton(
                    "Confirmar",
                    icon=ft.Icons.CHECK_ROUNDED,
                    on_click=lambda _: self._apply_boolean_toggle(dialog, record_id, field_name, new_value),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: Tema.SUCCESS if new_value else Tema.ERROR},
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

    def _cancel_boolean_toggle(self, dialog):
        self._close_dialog(dialog)
        self._build_crud_content()

    def _apply_boolean_toggle(self, dialog, record_id, field_name, new_value):
        try:
            db = SessionLocal()
            try:
                db.execute(
                    text(f"UPDATE {self.current_config['table']} SET {field_name} = :value WHERE {self.current_config['pk']} = :id"),
                    {"value": bool(new_value), "id": record_id},
                )
                db.commit()
            finally:
                db.close()
            self._close_dialog(dialog)
            self._build_crud_content()
            estado = "activado" if new_value else "desactivado"
            self._show_message("Cambio confirmado", f"{self.current_config['label']} {estado} correctamente", Tema.SUCCESS)
        except Exception as exc:
            self._close_dialog(dialog)
            self._show_message("No se pudo cambiar el estado", str(exc), Tema.ERROR)

    def _text_cell(self, value, column_name=None):
        if column_name and "url" in column_name and value:
            value = str(value).split("?")[0]
        return ft.DataCell(ft.Text(self._display(value), color=Tema.TEXT_SECONDARY, size=12, selectable=True))

    def _display_cell(self, value, column_name=None):
        if column_name == "codigo_hex" and value:
            return ft.DataCell(
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            width=18,
                            height=18,
                            border_radius=4,
                            bgcolor=str(value),
                            border=ft.Border(
                                left=ft.BorderSide(1, Tema.BORDER),
                                right=ft.BorderSide(1, Tema.BORDER),
                                top=ft.BorderSide(1, Tema.BORDER),
                                bottom=ft.BorderSide(1, Tema.BORDER),
                            ),
                        ),
                        ft.Text(self._display(value), color=Tema.TEXT_SECONDARY, size=12, selectable=True),
                    ],
                )
            )
        if column_name and any(token in column_name for token in ("estado", "status", "principal")):
            return self._status_cell(value)
        return self._text_cell(value, column_name)

    def _status_cell(self, value):
        text_value = self._display(value)
        color = Tema.TEXT_MUTED
        bg = "#F8FAFC"
        if text_value in ("Activo", "Normal", "Sí", "Entregado", "Pagado"):
            color = Tema.SUCCESS
            bg = "#ECFDF3"
        elif text_value in ("Stock bajo", "Pendiente", "En preparación", "En tránsito"):
            color = Tema.WARNING
            bg = Tema.GOLD_SOFT
        elif text_value in ("Agotado", "Inactivo", "No", "Cancelado", "Novedad"):
            color = Tema.ERROR
            bg = "#FEF3F2"
        return ft.DataCell(ft.Container(border_radius=6, padding=ft.Padding(8, 4, 8, 4), bgcolor=bg, content=ft.Text(text_value, color=color, size=11, weight=ft.FontWeight.W_700)))

    def _refresh_crud_table(self):
        if self.current_config:
            self._build_crud_content()

    def _edit_record(self, record):
        self._open_record_dialog(record)
        if self.current_config["table"] == "variantes_producto" and self.stock_variant_selector:
            self.stock_variant_selector.value = str(self.selected_record_id)

    def _clear_form(self):
        self.selected_record_id = None
        self.selected_record_text.value = "Registro seleccionado: ninguno"
        for field_name, field_type in self.current_config["fields"]:
            control = self.form_controls[field_name]
            control.value = "true" if field_type == "bool" else ""
        if self.current_config["table"] == "usuarios":
            for field_name in ["direccion_descripcion", "direccion_barrio", "direccion_municipio", "direccion_departamento"]:
                if field_name in self.form_controls:
                    self.form_controls[field_name].value = ""
            if "direccion_principal" in self.form_controls:
                self.form_controls["direccion_principal"].value = True
        if self.current_config["table"] == "variantes_producto" and self.stock_variant_selector:
            self.stock_variant_selector.value = ""
        self.crud_area.update()

    def _clear_dialog_error(self):
        if hasattr(self, "dialog_feedback") and self.dialog_feedback is not None:
            self.dialog_feedback.visible = False
            self.dialog_feedback.content = None

    def _show_dialog_error(self, message):
        message = self._friendly_error(message)
        if not hasattr(self, "dialog_feedback") or self.dialog_feedback is None:
            self._snack(message, Tema.ERROR)
            return
        self.dialog_feedback.visible = True
        self.dialog_feedback.bgcolor = "#FEF3F2"
        self.dialog_feedback.border_radius = 8
        self.dialog_feedback.padding = ft.Padding(12, 10, 12, 10)
        self.dialog_feedback.border = ft.Border(
            left=ft.BorderSide(4, Tema.ERROR),
            right=ft.BorderSide(1, "#FDA29B"),
            top=ft.BorderSide(1, "#FDA29B"),
            bottom=ft.BorderSide(1, "#FDA29B"),
        )
        self.dialog_feedback.content = ft.Row(
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(ft.Icons.ERROR_ROUNDED, color=Tema.ERROR, size=20),
                ft.Text(message, color=Tema.TEXT_PRIMARY, size=12, weight=ft.FontWeight.W_600, selectable=True, expand=True),
            ],
        )
        try:
            self.page.update()
        except RuntimeError:
            pass

    def _field_value(self, field_name):
        control = self.form_controls[field_name]
        value = control.value
        if field_name not in LOOKUP_CONFIG:
            return value
        if value in (None, "", "Sin seleccionar"):
            return None
        value_text = str(value)
        if value_text.isdigit():
            return value_text
        for option in control.options:
            if str(option.text).strip().lower() == value_text.strip().lower():
                return option.key
        return value

    def _validate_record(self, config, values):
        for field_name, field_type in config["fields"]:
            value = values.get(field_name)
            if self._field_required(config["table"], field_name) and value in (None, ""):
                raise ValueError(f"El campo {self._pretty(field_name)} es obligatorio")
            if value in (None, ""):
                continue
            if field_name == "correo_electronico" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(value)):
                raise ValueError("Ingresa un correo electrónico válido")
            if field_name == "telefono" and not re.fullmatch(r"\d{7,15}", str(value)):
                raise ValueError("El teléfono debe tener solo números entre 7 y 15 dígitos")
            if field_name == "codigo_hex" and not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(value)):
                raise ValueError("El código HEX debe tener formato #RRGGBB")
            if field_type == "int" and int(value) < 0:
                raise ValueError(f"{self._pretty(field_name)} no puede ser negativo")
            if field_type == "decimal" and Decimal(value) < 0:
                raise ValueError(f"{self._pretty(field_name)} no puede ser negativo")
            if field_name == "porcentaje_descuento" and Decimal(value) > 100:
                raise ValueError("El porcentaje de descuento no puede ser mayor a 100")
            if field_name in ("stock", "cantidad", "orden") and int(value) < 0:
                raise ValueError(f"{self._pretty(field_name)} no puede ser negativo")
            if field_name == "url_imagen" and not str(value).strip():
                raise ValueError("La URL de imagen es obligatoria")
        if config["table"] == "descuentos" and values.get("fecha_inicio") and values.get("fecha_fin"):
            today = date.today()
            if values["fecha_inicio"] < today or values["fecha_fin"] < today:
                raise ValueError("Los cupones solo pueden iniciar o terminar desde hoy en adelante")
            if values["fecha_fin"] < values["fecha_inicio"]:
                raise ValueError("La fecha fin debe ser mayor o igual a la fecha inicio")

    def _field_required(self, table, field_name):
        optional = {
            "id_coleccion",
            "descripcion_producto",
            "descripcion_categoria",
            "descripcion_coleccion",
            "descripcion",
            "codigo_hex",
            "telefono",
            "id_respuesta_bold",
            "referencia_documento",
            "observacion",
            "numero_guia",
            "transportadora",
            "fecha_envio",
            "fecha_entrega_estimada",
            "fecha_entrega_real",
            "raw_response",
            "payment_method",
        }
        if field_name == "contrasena_hash" and self.selected_record_id is not None:
            return False
        if field_name == "id_color" and table == "imagenes_producto":
            return False
        if field_name == "id_producto" and table == "descuentos":
            return False
        return field_name not in optional

    def _confirm_delete(self, record):
        self.selected_record_id = record[self.current_config["pk"]]
        title = self._record_title(record)
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor="#FFFFFF",
            elevation=18,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(spacing=10, controls=[
                        ft.Container(width=38, height=38, border_radius=9, bgcolor="#FEF3F2", alignment=ft.Alignment.CENTER, content=ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, color=Tema.ERROR, size=22)),
                        ft.Text("Confirmar eliminación", size=18, weight=ft.FontWeight.W_800, color=Tema.TEXT_PRIMARY),
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
                        ft.Text("Esta acción eliminará el registro seleccionado.", size=13, color=Tema.TEXT_SECONDARY),
                        ft.Container(
                            bgcolor="#F8FAFC",
                            border_radius=8,
                            padding=ft.Padding(12, 10, 12, 10),
                            border=ft.Border(left=ft.BorderSide(3, Tema.ERROR)),
                            content=ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY, selectable=True),
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_dialog(dialog)),
                ft.FilledButton(
                    "Eliminar",
                    icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                    on_click=lambda _: self._delete_record(record, dialog),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: Tema.ERROR, ft.ControlState.HOVERED: "#B42318"},
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.Padding(18, 11, 18, 11),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dialog.open = True
        if dialog not in self.page.overlay:
            self.page.overlay.append(dialog)
        self.page.update()

    def _record_title(self, record):
        candidates = [
            "nombre_producto",
            "nombre_categoria",
            "nombre_coleccion",
            "nombre_color",
            "nombre_medida",
            "descripcion_estado",
            "correo_electronico",
            "sku",
            "codigo",
            "transaction_id",
            "numero_guia",
            "producto",
            "cliente",
            "usuario",
        ]
        for key in candidates:
            if record.get(key):
                return str(record.get(key))
        for key, value in record.items():
            if not key.startswith("id_") and value not in (None, ""):
                return str(value)
        return f"{self.current_config['label']} #{record.get(self.current_config['pk'])}"

    def _panel(self, controls):
        return ft.Container(
            bgcolor=Tema.BG_CARD,
            border_radius=14,
            padding=18,
            border=ft.Border(
                left=ft.BorderSide(1, Tema.BORDER_SOFT),
                right=ft.BorderSide(1, Tema.BORDER_SOFT),
                top=ft.BorderSide(1, Tema.BORDER_SOFT),
                bottom=ft.BorderSide(1, Tema.BORDER_SOFT),
            ),
            shadow=ft.BoxShadow(blur_radius=22, color=ft.Colors.with_opacity(0.08, "#172033"), offset=ft.Offset(0, 9)),
            content=ft.Column(spacing=10, controls=controls),
        )

    def _table_panel(self, title, headings, rows):
        if not rows:
            rows = [ft.DataRow(cells=[ft.DataCell(ft.Text("Sin registros", color=Tema.TEXT_MUTED))] + [ft.DataCell(ft.Text("")) for _ in headings[1:]])]
        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=14,
            controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(title, size=14, color=Tema.TEXT_MUTED, weight=ft.FontWeight.W_700),
                    ft.Container(border_radius=20, bgcolor=Tema.GOLD_SOFT, padding=ft.Padding(10, 4, 10, 4), content=ft.Text("Tabla operativa", size=11, color=Tema.GOLD_DARK, weight=ft.FontWeight.W_700)),
                ]),
                ft.Container(
                    bgcolor=Tema.BG_CARD,
                    border_radius=16,
                    padding=16,
                    border=ft.Border(left=ft.BorderSide(1, Tema.BORDER_SOFT), right=ft.BorderSide(1, Tema.BORDER_SOFT), top=ft.BorderSide(1, Tema.BORDER_SOFT), bottom=ft.BorderSide(1, Tema.BORDER_SOFT)),
                    shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.08, "#172033"), offset=ft.Offset(0, 10)),
                    content=ft.Row(scroll=ft.ScrollMode.AUTO, controls=[
                        ft.DataTable(
                            columns=[ft.DataColumn(ft.Text(label, color=Tema.TEXT_SECONDARY, size=12, weight=ft.FontWeight.W_800)) for label in headings],
                            rows=rows,
                            heading_row_color=ft.Colors.with_opacity(0.96, Tema.BG_TABLE_HEAD),
                            data_row_color={
                                ft.ControlState.SELECTED: ft.Colors.with_opacity(0.95, "#FFF7E6"),
                                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.70, "#FFF4D8"),
                            },
                            divider_thickness=0.7,
                            column_spacing=28,
                        )
                    ]),
                ),
            ],
        )

    def _badge(self, text_value, color):
        return ft.Container(bgcolor=color, border_radius=6, padding=ft.Padding(8, 3, 8, 3), content=ft.Text(text_value, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.W_600))

    def _pretty(self, value):
        labels = {
            "id_usuario": "Usuario",
            "id_direccion": "Dirección",
            "id_estado_pedido": "Estado pedido",
            "id_estado_envio": "Estado envío",
            "id_producto": "Producto",
            "id_categoria": "Categoría",
            "id_coleccion": "Colección",
            "id_medida": "Medida",
            "id_color": "Color",
            "id_variante": "Variante",
            "id_pedido": "Pedido",
            "id_respuesta_bold": "Respuesta Bold",
            "estado_producto": "Estado producto",
            "is_active": "Estado",
            "es_principal": "Estado" if self.current_config and self.current_config.get("table") == "imagenes_producto" else "Principal",
            "estado": "Estado",
        }
        return labels.get(value, value.replace("id_", "").replace("_", " ").capitalize())

    def _display(self, value):
        if value is None:
            return "-"
        text_value = str(value)
        return text_value if len(text_value) <= 70 else text_value[:67] + "..."

    def _parse_value(self, value, field_type):
        if field_type == "bool":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("true", "1", "si", "sí", "activo", "activar")
        if value is None or str(value).strip() == "":
            return None
        if field_type == "int":
            return int(value)
        if field_type == "decimal":
            return Decimal(str(value).replace(",", ""))
        if field_type == "date":
            text_value = str(value).strip()
            return date.fromisoformat(text_value[:10])
        return str(value).strip()

    def _show_message(self, title, message, color):
        message = self._friendly_error(message)
        self._snack(f"{title}: {message}", color)
        try:
            page = self.page
        except RuntimeError:
            return
        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text(title),
            content=ft.Text(message, selectable=True),
            actions=[ft.TextButton("Aceptar", on_click=lambda _: self._close_dialog(dialog))],
        )
        try:
            page.open(dialog)
        except Exception:
            page.dialog = dialog
            dialog.open = True
            page.update()

    def _close_dialog(self, dialog):
        try:
            dialog.open = False
            self.page.update()
        except Exception:
            dialog.open = False
            try:
                self.page.update()
            except RuntimeError:
                pass

    def _feedback_icon(self, color):
        if color == Tema.ERROR:
            return ft.Icons.ERROR_ROUNDED
        if color == Tema.SUCCESS:
            return ft.Icons.CHECK_CIRCLE_ROUNDED
        return ft.Icons.INFO_ROUNDED

    def _feedback_background(self, color):
        if color == Tema.ERROR:
            return "#FEF3F2"
        if color == Tema.SUCCESS:
            return "#ECFDF3"
        return Tema.GOLD_SOFT

    def _feedback_border(self, color):
        if color == Tema.ERROR:
            return "#FDA29B"
        if color == Tema.SUCCESS:
            return "#75E0A7"
        return "#FDBA74"

    def _clear_feedback(self):
        self.feedback_banner.visible = False
        self.feedback_banner.content = None

    def _friendly_error(self, message):
        text_value = str(message)
        if "fecha_movimiento" in text_value and "NotNullViolation" in text_value:
            return "No se pudo registrar el Kardex porque la fecha del movimiento no se guardó. Ya quedó corregido para enviar fecha automática."
        if "duplicate key" in text_value or "UniqueViolation" in text_value:
            return "Ya existe un registro con esos datos únicos. Revisa SKU, correo, slug o referencia."
        if "ForeignKeyViolation" in text_value:
            return "El registro está relacionado con otra tabla o el ID seleccionado no existe."
        return text_value

    def _snack(self, message, color):
        message = self._friendly_error(message)
        self.feedback_banner.visible = True
        self.feedback_banner.bgcolor = self._feedback_background(color)
        self.feedback_banner.border_radius = 10
        self.feedback_banner.padding = ft.Padding(14, 12, 14, 12)
        self.feedback_banner.border = ft.Border(
            left=ft.BorderSide(4, color),
            right=ft.BorderSide(1, self._feedback_border(color)),
            top=ft.BorderSide(1, self._feedback_border(color)),
            bottom=ft.BorderSide(1, self._feedback_border(color)),
        )
        self.feedback_banner.content = ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(self._feedback_icon(color), color=color, size=22),
                ft.Text(message, color=Tema.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_600, selectable=True),
            ],
        )
        try:
            page = self.page
        except RuntimeError:
            return
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def _show_error(self, exc):
        self.content_area.content = self._panel([ft.Text("Error al cargar la vista", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        self._snack(str(exc), Tema.ERROR)

def _delegate_save_record(self, dialog=None):
    return self.controller.save_record(self, dialog)

def _delegate_delete_record(self, record=None, dialog=None):
    return self.controller.delete_record(self, record, dialog)

def _delegate_set_boolean(self, value):
    return self.controller.set_boolean(self, value)

def _delegate_update_selected(self, values, message):
    return self.controller.update_selected(self, values, message)

def _delegate_toggle_discount_active(self, discount_id, is_active):
    return self.controller.toggle_discount_active(self, discount_id, is_active)

BaseCrudView._save_record = _delegate_save_record
BaseCrudView._delete_record = _delegate_delete_record
BaseCrudView._set_boolean = _delegate_set_boolean
BaseCrudView._update_selected = _delegate_update_selected
BaseCrudView._toggle_discount_active = _delegate_toggle_discount_active

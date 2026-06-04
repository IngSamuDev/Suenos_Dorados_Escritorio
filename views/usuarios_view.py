import json
from pathlib import Path

import flet as ft
from sqlalchemy import text

from controllers.usuarios_controller import UsuariosController
from database import SessionLocal
from utils.theme import Tema
from views.crud_base_view import BaseCrudView


USUARIOS_GROUP = {'title': 'Usuarios y roles',
 'tables': [{'label': 'Usuarios',
             'table': 'usuarios',
             'pk': 'id_usuario',
             'fields': [('id_rol', 'int'),
                        ('nombre_usuario', 'str'),
                        ('apellido_usuario', 'str'),
                        ('correo_electronico', 'str'),
                        ('telefono', 'str'),
                        ('contrasena_hash', 'password'),
                        ('estado', 'bool')]},
            {'label': 'Direcciones',
             'table': 'direcciones',
             'pk': 'id_direccion',
             'fields': [('id_usuario', 'int'),
                        ('descripcion_direccion', 'str'),
                        ('descripcion_barrio', 'str'),
                        ('descripcion_departamento', 'str'),
                        ('descripcion_municipio', 'str'),
                        ('es_principal', 'bool')]},
            {'label': 'Roles', 'table': 'roles', 'pk': 'id_rol', 'fields': [('descripcion_rol', 'str')]}]}


LOCATIONS_DIR = Path(__file__).resolve().parents[1] / "utils"


def _load_location_data():
    try:
        departments = json.loads((LOCATIONS_DIR / "colombia_departments.json").read_text(encoding="utf-8"))["data"]
        cities = json.loads((LOCATIONS_DIR / "colombia_cities.json").read_text(encoding="utf-8"))["data"]
    except Exception:
        return [], {}

    departments = sorted(departments, key=lambda item: item["name"])
    department_ids = {item["name"]: item["id"] for item in departments}
    department_names_by_id = {item["id"]: item["name"] for item in departments}
    cities_by_department = {item["name"]: [] for item in departments}
    for city in cities:
        department_name = department_names_by_id.get(city["departmentId"])
        if department_name:
            cities_by_department[department_name].append(city["name"])
    for city_list in cities_by_department.values():
        city_list.sort()
    return departments, cities_by_department


COLOMBIA_DEPARTMENTS, COLOMBIA_CITIES_BY_DEPARTMENT = _load_location_data()


class UsuariosView(BaseCrudView):
    def __init__(self):
        self.controller = UsuariosController()
        super().__init__(self.controller.group_id, USUARIOS_GROUP)

    def _department_options(self):
        return [ft.dropdown.Option(key=item["name"], text=item["name"]) for item in COLOMBIA_DEPARTMENTS]

    def _municipality_options(self, department):
        return [ft.dropdown.Option(key=name, text=name) for name in COLOMBIA_CITIES_BY_DEPARTMENT.get(department, [])]

    def _build_department_dropdown(self, field_name, label, municipality_field):
        return ft.Dropdown(
            label=label,
            width=390,
            dense=True,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=260,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            options=self._department_options(),
            hint_text="Selecciona departamento",
            on_select=lambda _: self._refresh_municipality_options(field_name, municipality_field),
        )

    def _build_municipality_dropdown(self, label):
        return ft.Dropdown(
            label=label,
            width=390,
            dense=True,
            editable=True,
            enable_filter=True,
            enable_search=True,
            menu_height=260,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            options=[],
            hint_text="Primero selecciona departamento",
        )

    def _refresh_municipality_options(self, department_field, municipality_field, keep_value=False):
        department_control = self.form_controls.get(department_field)
        municipality_control = self.form_controls.get(municipality_field)
        if not department_control or not municipality_control:
            return
        current_value = municipality_control.value
        municipality_control.options = self._municipality_options(department_control.value)
        valid_values = {option.key for option in municipality_control.options}
        if not keep_value or current_value not in valid_values:
            municipality_control.value = ""
        else:
            municipality_control.value = current_value
        municipality_control.hint_text = "Selecciona municipio / ciudad" if department_control.value else "Primero selecciona departamento"
        try:
            municipality_control.update()
        except RuntimeError:
            pass

    def _build_field_control(self, field_name, field_type):
        if self.current_config["table"] == "direcciones":
            if field_name == "descripcion_departamento":
                return self._build_department_dropdown(field_name, self._pretty(field_name), "descripcion_municipio")
            if field_name == "descripcion_municipio":
                return self._build_municipality_dropdown(self._pretty(field_name))
        return super()._build_field_control(field_name, field_type)

    def _build_user_address_fields(self):
        address = ft.TextField(
            label="Dirección",
            width=390,
            dense=True,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
        )
        barrio = ft.TextField(
            label="Barrio",
            width=390,
            dense=True,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
        )
        department = self._build_department_dropdown("direccion_departamento", "Departamento", "direccion_municipio")
        municipality = self._build_municipality_dropdown("Municipio / Ciudad")
        self.form_controls["direccion_descripcion"] = address
        self.form_controls["direccion_barrio"] = barrio
        self.form_controls["direccion_departamento"] = department
        self.form_controls["direccion_municipio"] = municipality
        principal = ft.Checkbox(label="Dirección principal", value=True, fill_color=Tema.GOLD)
        self.form_controls["direccion_principal"] = principal
        return [
            ft.Container(height=4),
            ft.Text("Dirección principal", size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY),
            ft.Row([address, barrio], spacing=12, wrap=True),
            ft.Row([department, municipality], spacing=12, wrap=True),
            ft.Row([principal], spacing=12, wrap=True),
        ]

    def _fill_form_from_record(self, record):
        super()._fill_form_from_record(record)
        if self.current_config["table"] == "usuarios":
            self._refresh_municipality_options("direccion_departamento", "direccion_municipio", keep_value=True)
        if self.current_config["table"] == "direcciones":
            self._refresh_municipality_options("descripcion_departamento", "descripcion_municipio", keep_value=True)

    def _validate_location_pair(self, department, municipality):
        if department and department not in COLOMBIA_CITIES_BY_DEPARTMENT:
            raise ValueError("Selecciona un departamento válido")
        if department and municipality and municipality not in COLOMBIA_CITIES_BY_DEPARTMENT.get(department, []):
            raise ValueError("El municipio / ciudad no corresponde al departamento seleccionado")

    def _validate_record(self, config, values):
        super()._validate_record(config, values)
        if config["table"] == "direcciones":
            self._validate_location_pair(values.get("descripcion_departamento"), values.get("descripcion_municipio"))

    def _load_users_table(self, config):
        order_col = self.order_field.value if self.order_field and self.order_field.value in ["id_usuario", "id_rol", "nombre_usuario", "apellido_usuario", "correo_electronico", "telefono", "estado"] else "id_usuario"
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = """
                WHERE CAST(u.id_usuario AS TEXT) ILIKE :search
                   OR u.nombre_usuario ILIKE :search
                   OR u.apellido_usuario ILIKE :search
                   OR u.correo_electronico ILIKE :search
                   OR r.descripcion_rol ILIKE :search
                   OR COALESCE(u.telefono, '') ILIKE :search
                   OR COALESCE(d.descripcion_direccion, '') ILIKE :search
                   OR COALESCE(d.descripcion_barrio, '') ILIKE :search
                   OR COALESCE(d.descripcion_municipio, '') ILIKE :search
                   OR COALESCE(d.descripcion_departamento, '') ILIKE :search
            """
            params["search"] = f"%{search_value}%"
        sql = f"""
            SELECT
                u.id_usuario,
                u.id_rol,
                u.nombre_usuario,
                u.apellido_usuario,
                u.correo_electronico,
                u.telefono,
                u.estado,
                r.descripcion_rol,
                d.descripcion_direccion,
                d.descripcion_barrio,
                d.descripcion_municipio,
                d.descripcion_departamento,
                d.es_principal
            FROM usuarios u
            LEFT JOIN roles r ON r.id_rol = u.id_rol
            LEFT JOIN LATERAL (
                SELECT descripcion_direccion, descripcion_barrio, descripcion_municipio, descripcion_departamento, es_principal
                FROM direcciones
                WHERE id_usuario = u.id_usuario
                ORDER BY es_principal DESC, id_direccion DESC
                LIMIT 1
            ) d ON TRUE
            {where_sql}
            ORDER BY u.{order_col} DESC
            LIMIT 35
        """
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar usuarios", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        rows = []
        for item in rows_data:
            record = dict(item)
            display_values = [
                record.get("descripcion_rol"),
                f"{record.get('nombre_usuario', '')} {record.get('apellido_usuario', '')}".strip(),
                record.get("correo_electronico"),
                record.get("telefono"),
                record.get("descripcion_direccion"),
                record.get("descripcion_barrio"),
                record.get("descripcion_municipio"),
                record.get("descripcion_departamento"),
                "Activo" if record.get("estado") else "Inactivo",
            ]
            rows.append(ft.DataRow(cells=[self._action_cell(record)] + [self._status_cell(value) if value in ("Activo", "Inactivo") else self._text_cell(value) for value in display_values]))
        return self._table_panel(f"{len(rows_data)} usuarios", ["Acciones", "Rol", "Usuario", "Correo", "Teléfono", "Dirección", "Barrio", "Municipio", "Departamento", "Estado"], rows)

    def _load_addresses_table(self, config):
        order_col = self.order_field.value if self.order_field and self.order_field.value in ["id_direccion", "id_usuario", "descripcion_municipio", "descripcion_departamento"] else "id_direccion"
        search_value = (self.search_field.value or "").strip() if self.search_field else ""
        where_sql = ""
        params = {}
        if search_value:
            where_sql = """
                WHERE CAST(d.id_direccion AS TEXT) ILIKE :search
                   OR CAST(d.id_usuario AS TEXT) ILIKE :search
                   OR u.nombre_usuario ILIKE :search
                   OR u.apellido_usuario ILIKE :search
                   OR u.correo_electronico ILIKE :search
                   OR d.descripcion_direccion ILIKE :search
                   OR d.descripcion_barrio ILIKE :search
                   OR d.descripcion_municipio ILIKE :search
                   OR d.descripcion_departamento ILIKE :search
            """
            params["search"] = f"%{search_value}%"
        sql = f"""
            SELECT
                d.id_direccion,
                d.id_usuario,
                u.nombre_usuario,
                u.apellido_usuario,
                u.correo_electronico,
                d.descripcion_direccion,
                d.descripcion_barrio,
                d.descripcion_municipio,
                d.descripcion_departamento,
                d.es_principal
            FROM direcciones d
            JOIN usuarios u ON u.id_usuario = d.id_usuario
            {where_sql}
            ORDER BY d.{order_col} DESC
            LIMIT 35
        """
        try:
            db = SessionLocal()
            try:
                rows_data = db.execute(text(sql), params).mappings().all()
            finally:
                db.close()
        except Exception as exc:
            return self._panel([ft.Text("No se pudo cargar direcciones", color=Tema.ERROR, weight=ft.FontWeight.W_700), ft.Text(str(exc), color=Tema.TEXT_MUTED, size=12)])
        rows = []
        for item in rows_data:
            record = dict(item)
            usuario = f"{record.get('nombre_usuario', '')} {record.get('apellido_usuario', '')}".strip()
            display_values = [
                usuario,
                record.get("correo_electronico"),
                record.get("descripcion_direccion"),
                record.get("descripcion_barrio"),
                record.get("descripcion_municipio"),
                record.get("descripcion_departamento"),
                "Sí" if record.get("es_principal") else "No",
            ]
            rows.append(ft.DataRow(cells=[self._action_cell(record)] + [self._status_cell(value) if value in ("Sí", "No") else self._text_cell(value) for value in display_values]))
        return self._table_panel(f"{len(rows_data)} direcciones", ["Acciones", "Usuario", "Correo", "Dirección", "Barrio", "Municipio", "Departamento", "Principal"], rows)

    def _save_user_address(self, db, user_id):
        address = (self.form_controls.get("direccion_descripcion").value or "").strip() if self.form_controls.get("direccion_descripcion") else ""
        barrio = (self.form_controls.get("direccion_barrio").value or "").strip() if self.form_controls.get("direccion_barrio") else ""
        municipio = (self.form_controls.get("direccion_municipio").value or "").strip() if self.form_controls.get("direccion_municipio") else ""
        departamento = (self.form_controls.get("direccion_departamento").value or "").strip() if self.form_controls.get("direccion_departamento") else ""
        principal = bool(self.form_controls.get("direccion_principal").value) if self.form_controls.get("direccion_principal") else True
        if not any([address, barrio, municipio, departamento]):
            return
        if not address or not municipio or not departamento:
            raise ValueError("Para guardar dirección debes llenar Dirección, Municipio/Ciudad y Departamento")
        self._validate_location_pair(departamento, municipio)
        if principal:
            db.execute(text("UPDATE direcciones SET es_principal = FALSE WHERE id_usuario = :user_id"), {"user_id": user_id})
        existing_id = db.execute(
            text("""
                SELECT id_direccion
                FROM direcciones
                WHERE id_usuario = :user_id
                ORDER BY es_principal DESC, id_direccion DESC
                LIMIT 1
            """),
            {"user_id": user_id},
        ).scalar()
        params = {
            "user_id": user_id,
            "address": address,
            "barrio": barrio or None,
            "municipio": municipio,
            "departamento": departamento,
            "principal": principal,
        }
        if existing_id:
            db.execute(
                text("""
                    UPDATE direcciones
                    SET descripcion_direccion = :address,
                        descripcion_barrio = :barrio,
                        descripcion_municipio = :municipio,
                        descripcion_departamento = :departamento,
                        es_principal = :principal
                    WHERE id_direccion = :address_id
                """),
                {**params, "address_id": existing_id},
            )
        else:
            db.execute(
                text("""
                    INSERT INTO direcciones
                        (id_usuario, descripcion_direccion, descripcion_barrio, descripcion_municipio, descripcion_departamento, es_principal)
                    VALUES
                        (:user_id, :address, :barrio, :municipio, :departamento, :principal)
                """),
                params,
            )

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
                        ('descripcion_municipio', 'str'),
                        ('descripcion_departamento', 'str'),
                        ('es_principal', 'bool')]},
            {'label': 'Roles', 'table': 'roles', 'pk': 'id_rol', 'fields': [('descripcion_rol', 'str')]}]}


class UsuariosView(BaseCrudView):
    def __init__(self):
        self.controller = UsuariosController()
        super().__init__(self.controller.group_id, USUARIOS_GROUP)

    def _build_user_address_fields(self):
        address_fields = [
            ("direccion_descripcion", "Dirección", "str"),
            ("direccion_barrio", "Barrio", "str"),
            ("direccion_municipio", "Municipio / Ciudad", "str"),
            ("direccion_departamento", "Departamento", "str"),
        ]
        controls = []
        for key, label, _ in address_fields:
            control = ft.TextField(
                label=label,
                width=390,
                dense=True,
                border_color=Tema.BORDER,
                focused_border_color=Tema.GOLD,
                bgcolor="#FFFFFF",
                color=Tema.TEXT_PRIMARY,
            )
            self.form_controls[key] = control
            controls.append(control)
        principal = ft.Checkbox(label="Dirección principal", value=True, fill_color=Tema.GOLD)
        self.form_controls["direccion_principal"] = principal
        return [
            ft.Container(height=4),
            ft.Text("Dirección principal", size=13, weight=ft.FontWeight.W_700, color=Tema.TEXT_PRIMARY),
            ft.Row(controls[:3], spacing=12, wrap=True),
            ft.Row([controls[3], principal], spacing=12, wrap=True),
        ]

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

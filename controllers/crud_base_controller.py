from sqlalchemy import text

from database import SessionLocal
from utils.security import hash_password
from utils.theme import Tema


class BaseCrudController:
    """Lógica común de CRUD usada por las vistas administrativas."""

    group_id = None

    def save_record(self, view, dialog=None):
        config = view.current_config
        try:
            view._clear_dialog_error()
            values = {}
            for field, field_type in config["fields"]:
                try:
                    raw_value = view._field_value(field)
                    values[field] = view._parse_value(raw_value, field_type)
                except Exception:
                    raise ValueError(f"El campo {view._pretty(field)} debe tener un formato válido")
            view._validate_record(config, values)
            if config["table"] == "usuarios":
                raw_password = values.get("contrasena_hash")
                if raw_password:
                    password_text = str(raw_password)
                    if not password_text.startswith(("$2a$", "$2b$", "$2y$")):
                        values["contrasena_hash"] = hash_password(password_text)
                elif view.selected_record_id is not None:
                    values.pop("contrasena_hash", None)
            is_new = view.selected_record_id is None
            db = SessionLocal()
            try:
                if is_new:
                    fields = list(values.keys())
                    result = db.execute(text(f"INSERT INTO {config['table']} ({', '.join(fields)}) VALUES ({', '.join(':' + f for f in fields)}) RETURNING {config['pk']}"), values)
                    saved_record_id = result.scalar()
                else:
                    assignments = ", ".join(f"{field} = :{field}" for field in values)
                    db.execute(text(f"UPDATE {config['table']} SET {assignments} WHERE {config['pk']} = :record_id"), {**values, "record_id": view.selected_record_id})
                    saved_record_id = view.selected_record_id
                if config["table"] == "usuarios":
                    view._save_user_address(db, saved_record_id)
                db.commit()
            finally:
                db.close()
            view._clear_form()
            view._build_crud_content()
            if dialog is not None:
                view._close_dialog(dialog)
            action = "creado" if is_new else "actualizado"
            view._snack(f"{config['label']} {action} correctamente", Tema.SUCCESS)
        except Exception as exc:
            if dialog is not None:
                view._show_dialog_error(f"No se pudo guardar {config['label']}: {exc}")
            else:
                view._snack(f"No se pudo guardar {config['label']}: {exc}", Tema.ERROR)

    def delete_record(self, view, record=None, dialog=None):
        record_id = record.get(view.current_config["pk"]) if record else view.selected_record_id
        if record_id is None:
            view._snack("Selecciona un registro primero", Tema.WARNING)
            return
        label = view.current_config["label"]
        try:
            db = SessionLocal()
            try:
                db.execute(text(f"DELETE FROM {view.current_config['table']} WHERE {view.current_config['pk']} = :id"), {"id": record_id})
                db.commit()
            finally:
                db.close()
            if dialog is not None:
                view._close_dialog(dialog)
            view.selected_record_id = None
            view.selected_record_text.value = "Registro seleccionado: ninguno"
            view._build_crud_content()
            view._snack(f"{label} eliminado correctamente", Tema.SUCCESS)
        except Exception as exc:
            view._snack(f"No se pudo eliminar {label}. Puede tener registros relacionados: {exc}", Tema.ERROR)

    def set_boolean(self, view, value):
        if view.selected_record_id is None:
            view._snack("Selecciona un registro primero", Tema.WARNING)
            return
        bool_fields = [name for name, kind in view.current_config["fields"] if kind == "bool"]
        if not bool_fields:
            view._snack("Esta tabla no tiene campo de habilitación", Tema.WARNING)
            return
        estado = "activado" if value else "desactivado"
        self.update_selected(view, {bool_fields[-1]: value}, f"{view.current_config['label']} {estado} correctamente")

    def update_selected(self, view, values, message):
        db = SessionLocal()
        try:
            assignments = ", ".join(f"{k} = :{k}" for k in values)
            db.execute(text(f"UPDATE {view.current_config['table']} SET {assignments} WHERE {view.current_config['pk']} = :record_id"), {**values, "record_id": view.selected_record_id})
            db.commit()
        finally:
            db.close()
        view._build_crud_content()
        view._snack(message, Tema.SUCCESS)

    def toggle_discount_active(self, view, discount_id, is_active):
        try:
            db = SessionLocal()
            try:
                db.execute(text("UPDATE descuentos SET is_active = :is_active WHERE id = :id"), {"is_active": bool(is_active), "id": discount_id})
                db.commit()
            finally:
                db.close()
            view._build_crud_content()
            estado = "activado" if is_active else "desactivado"
            view._snack(f"Descuento {estado} correctamente", Tema.SUCCESS)
        except Exception as exc:
            view._snack(f"No se pudo cambiar el estado del descuento: {exc}", Tema.ERROR)

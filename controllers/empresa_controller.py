import json
from pathlib import Path

from config import APP_NAME, APP_SUBTITLE, BASE_DIR
from models.empresa_model import EmpresaInfo


class EmpresaController:
    def __init__(self, config_file=None):
        self.config_file = Path(config_file or BASE_DIR / "empresa_config.json")

    def get_info(self):
        if not self.config_file.exists():
            return EmpresaInfo(nombre=APP_NAME, subtitulo=APP_SUBTITLE)
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
        except Exception:
            return EmpresaInfo(nombre=APP_NAME, subtitulo=APP_SUBTITLE)
        defaults = EmpresaInfo(nombre=APP_NAME, subtitulo=APP_SUBTITLE)
        payload = {field: data.get(field, getattr(defaults, field)) for field in defaults.__dataclass_fields__}
        return EmpresaInfo(**payload)

    def save_info(self, data):
        info = EmpresaInfo(**{field: str(data.get(field, "")).strip() for field in EmpresaInfo.__dataclass_fields__})
        self.config_file.write_text(json.dumps(info.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        return info

from dataclasses import dataclass


@dataclass
class EmpresaInfo:
    nombre: str = "Sueños Dorados"
    subtitulo: str = "Gestión Administrativa"
    nit: str = "900.000.000-1"
    direccion: str = "Calle 10 # 25-40"
    ciudad: str = "Cali"
    contacto: str = "contacto@suenosdorados.com"
    telefono: str = "300 000 0000"
    actividad: str = "E-commerce textil"

    @property
    def header_line(self):
        parts = [f"NIT {self.nit}", self.direccion, self.actividad]
        return " | ".join(part for part in parts if part)

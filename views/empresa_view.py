import flet as ft

from controllers.empresa_controller import EmpresaController
from utils.theme import Tema


class EmpresaView(ft.Container):
    def __init__(self):
        super().__init__()
        self.controller = EmpresaController()
        self.info = self.controller.get_info()
        self.feedback = ft.Text("", size=12, color=Tema.SUCCESS, visible=False)
        self.fields = {}
        self.expand = True
        self.bgcolor = Tema.BG_PRIMARY
        self.content = self._build()

    def _field(self, key, label, icon):
        field = ft.TextField(
            label=label,
            value=getattr(self.info, key),
            prefix_icon=icon,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor="#FFFFFF",
            color=Tema.TEXT_PRIMARY,
            dense=True,
        )
        self.fields[key] = field
        return ft.Container(col={"xs": 12, "md": 6}, content=field)

    def _build(self):
        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Container(
                    bgcolor=Tema.BG_SIDEBAR,
                    border_radius=16,
                    padding=24,
                    shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.16, "#172033"), offset=ft.Offset(0, 10)),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(spacing=5, controls=[
                                ft.Text("Información de la empresa", size=22, weight=ft.FontWeight.W_800, color=Tema.TEXT_ON_DARK),
                                ft.Text("Estos datos alimentan el encabezado del panel administrativo.", size=13, color=ft.Colors.with_opacity(0.78, Tema.TEXT_ON_DARK)),
                            ]),
                            ft.Icon(ft.Icons.BUSINESS_ROUNDED, color=Tema.GOLD, size=34),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor=Tema.BG_CARD,
                    border_radius=14,
                    padding=20,
                    border=ft.Border(
                        left=ft.BorderSide(1, Tema.BORDER_SOFT),
                        right=ft.BorderSide(1, Tema.BORDER_SOFT),
                        top=ft.BorderSide(1, Tema.BORDER_SOFT),
                        bottom=ft.BorderSide(1, Tema.BORDER_SOFT),
                    ),
                    shadow=ft.BoxShadow(blur_radius=22, color=ft.Colors.with_opacity(0.08, "#172033"), offset=ft.Offset(0, 9)),
                    content=ft.Column(spacing=16, controls=[
                        ft.ResponsiveRow(spacing=14, run_spacing=14, controls=[
                            self._field("nombre", "Nombre de la empresa", ft.Icons.STORE_ROUNDED),
                            self._field("subtitulo", "Subtítulo del sistema", ft.Icons.DASHBOARD_ROUNDED),
                            self._field("nit", "NIT", ft.Icons.BADGE_ROUNDED),
                            self._field("direccion", "Dirección", ft.Icons.LOCATION_ON_ROUNDED),
                            self._field("ciudad", "Ciudad", ft.Icons.MAP_ROUNDED),
                            self._field("contacto", "Correo de contacto", ft.Icons.EMAIL_ROUNDED),
                            self._field("telefono", "Teléfono", ft.Icons.PHONE_ROUNDED),
                            self._field("actividad", "Actividad / descripción", ft.Icons.WORK_ROUNDED),
                        ]),
                        self.feedback,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.FilledButton(
                                    "Guardar información",
                                    icon=ft.Icons.SAVE_ROUNDED,
                                    on_click=lambda _: self._save(),
                                    style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.DEFAULT: Tema.GOLD, ft.ControlState.HOVERED: Tema.GOLD_DARK},
                                        color=ft.Colors.WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                )
                            ],
                        ),
                    ]),
                ),
            ],
        )

    def _save(self):
        self.info = self.controller.save_info({key: field.value for key, field in self.fields.items()})
        self.feedback.value = "Información guardada. Vuelve al Dashboard para ver el encabezado actualizado."
        self.feedback.visible = True
        try:
            self.update()
        except RuntimeError:
            pass

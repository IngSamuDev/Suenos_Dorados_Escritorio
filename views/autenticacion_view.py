import flet as ft

from config import APP_NAME, APP_SUBTITLE, LOGO_FILE
from utils.theme import Tema


class AuthView(ft.Container):
    """Pantalla de inicio de sesión administrativa."""

    def __init__(self, controller, on_login_success):
        super().__init__()
        self.controller = controller
        self.on_login_success = on_login_success

        self.email_field = ft.TextField(
            label="Correo electrónico",
            hint_text="admin@gmail.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor=Tema.BG_INPUT,
            label_style=ft.TextStyle(color=Tema.TEXT_MUTED, size=13),
            hint_style=ft.TextStyle(color=Tema.TEXT_MUTED, size=13),
            text_style=ft.TextStyle(color=Tema.TEXT_PRIMARY, size=15),
            cursor_color=Tema.GOLD,
            border_radius=10,
            width=300,
            height=48,
            autofocus=True,
            on_submit=self.handle_login,
        )
        self.password_field = ft.TextField(
            label="Contraseña",
            hint_text="••••••••",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            border_color=Tema.BORDER,
            focused_border_color=Tema.GOLD,
            bgcolor=Tema.BG_INPUT,
            label_style=ft.TextStyle(color=Tema.TEXT_MUTED, size=13),
            hint_style=ft.TextStyle(color=Tema.TEXT_MUTED, size=13),
            text_style=ft.TextStyle(color=Tema.TEXT_PRIMARY, size=15),
            cursor_color=Tema.GOLD,
            border_radius=10,
            width=300,
            height=48,
            on_submit=self.handle_login,
        )
        self.error_text = ft.Text("", color=Tema.ERROR, size=13, visible=False, text_align=ft.TextAlign.CENTER)
        self.loading = ft.ProgressRing(width=22, height=22, color=Tema.GOLD, visible=False)
        self.login_btn = ft.FilledButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[ft.Icon(ft.Icons.LOGIN_ROUNDED, color=ft.Colors.WHITE), ft.Text("Ingresar", color=ft.Colors.WHITE, weight=ft.FontWeight.W_700)],
            ),
            width=300,
            height=48,
            on_click=self.handle_login,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: Tema.GOLD, ft.ControlState.HOVERED: Tema.GOLD_DARK},
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        card = ft.Container(
            width=372,
            height=462,
            padding=ft.Padding(30, 24, 30, 24),
            bgcolor=Tema.BG_CARD,
            border_radius=14,
            border=ft.Border(
                left=ft.BorderSide(1, Tema.BORDER),
                right=ft.BorderSide(1, Tema.BORDER),
                top=ft.BorderSide(1, Tema.BORDER),
                bottom=ft.BorderSide(1, Tema.BORDER),
            ),
            shadow=ft.BoxShadow(blur_radius=28, color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK), offset=ft.Offset(0, 12)),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    self._logo_box(74),
                    ft.Text(APP_NAME, size=23, weight=ft.FontWeight.BOLD, color=Tema.TEXT_PRIMARY),
                    ft.Text(APP_SUBTITLE, size=13, color=Tema.TEXT_MUTED),
                    ft.Container(height=4),
                    self.email_field,
                    self.password_field,
                    self.error_text,
                    ft.Row([self.login_btn, self.loading], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                ],
            ),
        )

        self.expand = True
        self.bgcolor = Tema.BG_PRIMARY
        self.content = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(24, 24, 24, 24),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[card],
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

    def handle_login(self, event):
        self.error_text.visible = False
        email = self.email_field.value.strip() if self.email_field.value else ""
        password = self.password_field.value if self.password_field.value else ""
        if not email or not password:
            self.error_text.value = "Todos los campos son obligatorios"
            self.error_text.visible = True
            self.update()
            return

        self.login_btn.disabled = True
        self.loading.visible = True
        self.update()
        usuario = self.controller.login(email, password)
        self.login_btn.disabled = False
        self.loading.visible = False

        if usuario:
            self.on_login_success(usuario)
        else:
            self.error_text.value = "Credenciales incorrectas. Verifica tu correo y contraseña."
            self.error_text.visible = True
            self.update()





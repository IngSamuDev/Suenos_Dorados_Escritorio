import flet as ft

from controllers.autenticacion_controller import AuthController
from database import Base, SessionLocal, engine
from models import *
from views.autenticacion_view import AuthView
from views.panel_view import DashboardView

async def main(page: ft.Page):
    page.title = "Sueños Dorados - Admin"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed="#E7A21B", use_material3=True, font_family="Inter")
    page.dark_theme = ft.Theme(color_scheme_seed="#E7A21B", use_material3=True, font_family="Inter")
    page.padding = 0
    page.bgcolor = "#F2F4F7"

    page.window.title_bar_hidden = False
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 640
    await page.window.center()

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    auth_ctrl = AuthController(db)
    try:
        auth_ctrl.init_admin()
    except Exception as exc:
        page.snack_bar = ft.SnackBar(ft.Text(f"No se pudo inicializar admin: {exc}"), bgcolor=ft.Colors.RED_700)
        page.snack_bar.open = True

    def go_dashboard(usuario):
        page.clean()
        page.add(DashboardView(usuario, on_logout=go_login))
        page.update()

    def go_login():
        page.clean()
        page.add(AuthView(auth_ctrl, on_login_success=go_dashboard))
        page.update()

    page.on_close = lambda _: db.close()
    go_login()


if __name__ == "__main__":
    ft.run(main)






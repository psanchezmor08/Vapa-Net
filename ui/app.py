"""
VapaNet — Shell principal de la aplicación (sidebar + navegación)
Compatible con Flet 0.21.x, 0.22.x, 0.23.x, 0.24.x
"""

import flet as ft
from ui import theme as T
from core import db


def _set_window(page: ft.Page, width, height, min_width, min_height):
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = width
            page.window.height = height
            page.window.min_width = min_width
            page.window.min_height = min_height
            return
        except Exception:
            pass
    for attr, val in [
        ("window_width", width), ("window_height", height),
        ("window_min_width", min_width), ("window_min_height", min_height),
    ]:
        try:
            setattr(page, attr, val)
        except Exception:
            pass


def _center_align():
    if hasattr(ft.alignment, "center"):
        return ft.alignment.center
    return ft.Alignment(0, 0)


class VapaNetApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._current_view = "dashboard"
        self._content_area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        self._nav_items = {}

    def initialize(self):
        p = self.page
        p.title = "VapaNet · Vapa"
        p.bgcolor = T.DARK_BG
        p.padding = 0
        p.spacing = 0

        _set_window(p, 1100, 720, 800, 550)
        db.initialize_db()

        topbar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Text("V", size=16, weight=ft.FontWeight.W_500, color=T.DARK_BG),
                        bgcolor=T.LIME,
                        width=30, height=30,
                        border_radius=8,
                        alignment=_center_align(),
                    ),
                    ft.Column([
                        ft.Text("VapaNet", size=15, weight=ft.FontWeight.W_500, color=T.LIME),
                        ft.Text("Network Intelligence Suite", size=10, color=T.TEXT_MUTED),
                    ], spacing=0, tight=True),
                ], spacing=10),
                ft.Row(expand=True),
                ft.Row([
                    ft.Container(width=7, height=7, bgcolor=T.STATUS_UP, border_radius=4),
                    ft.Text("Sistema activo", size=11, color=T.TEXT_MUTED),
                ], spacing=6),
                ft.Text("v1.0", size=11, color=T.LIME_MUTED),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=T.DARK_SURFACE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, T.DARK_BORDER)),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        )

        nav_def = [
            ("dashboard",  "Dashboard",          ft.icons.GRID_VIEW_ROUNDED, ""),
            ("__sep1__",   "",                   None,                       "Herramientas"),
            ("speed",      "Speed Test",         ft.icons.SPEED,             ""),
            ("ping",       "Ping",               ft.icons.WIFI_TETHERING,    ""),
            ("ports",      "Escáner de Puertos", ft.icons.RADAR,             ""),
            ("dns",        "DNS Lookup",         ft.icons.DNS,               ""),
            ("traceroute", "Traceroute",          ft.icons.ROUTE,             ""),
            ("batch",      "Batch Ping",         ft.icons.PLAYLIST_PLAY,     ""),
            ("__sep2__",   "",                   None,                       "Monitorización"),
            ("sentinel",   "Sentinel",           ft.icons.VISIBILITY,        ""),
            ("monitor",    "Monitor URLs",       ft.icons.LINK,              ""),
            ("__sep3__",   "",                   None,                       "Utilidades"),
            ("subnet",     "Subnet Calc",        ft.icons.CALCULATE,         ""),
            ("whois",      "WHOIS",              ft.icons.INFO_OUTLINE,      ""),
        ]

        sidebar_controls = []
        for key, label, icon, section in nav_def:
            if key.startswith("__sep"):
                sidebar_controls.append(T.section_label(section))
                continue
            is_active = (key == "dashboard")
            row = ft.Row([
                ft.Icon(icon, size=16, color=T.LIME if is_active else T.TEXT_SECONDARY),
                ft.Text(label, size=13, color=T.LIME if is_active else T.TEXT_SECONDARY, expand=True),
            ], spacing=9)
            item = ft.Container(
                content=row,
                bgcolor=T.DARK_HOVER if is_active else "transparent",
                border=ft.border.all(1, T.DARK_BORDER2 if is_active else "transparent"),
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                on_click=lambda e, k=key: self._navigate(k),
                ink=True,
                margin=ft.margin.only(bottom=1),
            )
            self._nav_items[key] = item
            sidebar_controls.append(
                ft.Container(content=item, padding=ft.padding.symmetric(horizontal=8))
            )

        sidebar = ft.Container(
            content=ft.Column(sidebar_controls, spacing=0, scroll=ft.ScrollMode.AUTO),
            bgcolor=T.DARK_SURFACE,
            border=ft.border.only(right=ft.border.BorderSide(1, T.DARK_BORDER)),
            width=210,
            padding=ft.padding.only(top=8, bottom=8),
        )

        content_wrapper = ft.Container(
            content=self._content_area,
            expand=True,
            padding=20,
            bgcolor=T.DARK_BG,
        )

        body = ft.Row([sidebar, content_wrapper], spacing=0, expand=True)
        p.add(ft.Column([topbar, body], spacing=0, expand=True))
        self._navigate("dashboard")
        p.update()

    def _navigate(self, key: str):
        for k, container in self._nav_items.items():
            active = (k == key)
            row = container.content
            row.controls[0].color = T.LIME if active else T.TEXT_SECONDARY
            row.controls[1].color = T.LIME if active else T.TEXT_SECONDARY
            container.bgcolor = T.DARK_HOVER if active else "transparent"
            container.border = ft.border.all(1, T.DARK_BORDER2 if active else "transparent")

        self._current_view = key
        self._content_area.controls.clear()
        self._content_area.controls.append(self._build_view(key))
        try:
            self.page.update()
        except Exception:
            pass

    def _build_view(self, key: str) -> ft.Control:
        from ui.views.dashboard  import DashboardView
        from ui.views.speedtest  import SpeedTestView
        from ui.views.ping       import PingView
        from ui.views.ports      import PortScanView
        from ui.views.dns        import DNSView
        from ui.views.traceroute import TracerouteView
        from ui.views.batch      import BatchPingView
        from ui.views.sentinel   import SentinelView
        from ui.views.monitor    import MonitorView
        from ui.views.subnet     import SubnetView
        from ui.views.whois      import WhoisView

        views = {
            "dashboard":  lambda: DashboardView(navigate_fn=self._navigate),
            "speed":      SpeedTestView,
            "ping":       PingView,
            "ports":      PortScanView,
            "dns":        DNSView,
            "traceroute": TracerouteView,
            "batch":      BatchPingView,
            "sentinel":   SentinelView,
            "monitor":    MonitorView,
            "subnet":     SubnetView,
            "whois":      WhoisView,
        }
        factory = views.get(key, lambda: ft.Text("Vista no encontrada", color=T.TEXT_MUTED))
        return factory()

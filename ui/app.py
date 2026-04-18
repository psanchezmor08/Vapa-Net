"""
VapaNet — Shell principal de la aplicación (sidebar + navegación)
Compatible con Flet 0.80+
"""

import flet as ft
from ui import theme as T
from core import db


def _set_window(page: ft.Page, width, height, min_width, min_height):
    try:
        page.window.width = width
        page.window.height = height
        page.window.min_width = min_width
        page.window.min_height = min_height
    except Exception:
        pass


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
                        alignment=ft.alignment.Alignment(0, 0),
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
                ft.Text("v2.0", size=11, color=T.LIME_MUTED),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=T.DARK_SURFACE,
            border=ft.Border.only(bottom=ft.BorderSide(1, T.DARK_BORDER)),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        )

        nav_def = [
            ("dashboard",  "Dashboard",          ft.Icons.GRID_VIEW_ROUNDED,  ""),
            ("__sep1__",   "",                   None,                         "Herramientas"),
            ("speed",      "Speed Test",         ft.Icons.SPEED,               ""),
            ("ping",       "Ping",               ft.Icons.WIFI_TETHERING,      ""),
            ("ports",      "Escáner de Puertos", ft.Icons.RADAR,               ""),
            ("dns",        "DNS Lookup",         ft.Icons.DNS,                 ""),
            ("traceroute", "Traceroute",         ft.Icons.ROUTE,               ""),
            ("batch",      "Batch Ping",         ft.Icons.PLAYLIST_PLAY,       ""),
            ("__sep2__",   "",                   None,                         "Monitorización"),
            ("sentinel",   "Sentinel",           ft.Icons.VISIBILITY,          ""),
            ("monitor",    "Monitor URLs",       ft.Icons.LINK,                ""),
            ("__sep3__",   "",                   None,                         "Utilidades"),
            ("subnet",     "Subnet Calc",        ft.Icons.CALCULATE,           ""),
            ("whois",      "WHOIS",              ft.Icons.INFO_OUTLINE,        ""),
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
                border=ft.Border.all(1, T.DARK_BORDER2 if is_active else "transparent"),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                on_click=lambda e, k=key: self._navigate(k),
                ink=True,
                margin=ft.Margin.only(bottom=1),
            )
            self._nav_items[key] = item
            sidebar_controls.append(
                ft.Container(content=item, padding=ft.Padding.symmetric(horizontal=8))
            )

        sidebar = ft.Container(
            content=ft.Column(sidebar_controls, spacing=0, scroll=ft.ScrollMode.AUTO),
            bgcolor=T.DARK_SURFACE,
            border=ft.Border.only(right=ft.BorderSide(1, T.DARK_BORDER)),
            width=210,
            padding=ft.Padding.only(top=8, bottom=8),
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
            container.border = ft.Border.all(1, T.DARK_BORDER2 if active else "transparent")

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

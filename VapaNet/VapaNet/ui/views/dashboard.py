"""
VapaNet — Vista Dashboard (pantalla de inicio)
"""

import flet as ft
from ui import theme as T
from core import db


class DashboardView(ft.Column):
    def __init__(self, navigate_fn):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self.navigate = navigate_fn
        self._build()

    def _build(self):
        history = db.get_speed_history(1)
        last = history[0] if history else None

        dl = f"{last['download_mbps']:.1f}" if last else "—"
        ul = f"{last['upload_mbps']:.1f}" if last else "—"
        ping = f"{last['ping_ms']:.0f}" if last else "—"
        ts = last["timestamp"][:16].replace("T", " ") if last else "Sin datos"

        sentinel = db.get_sentinel_hosts()
        monitor = db.get_monitor_urls()
        down_count = sum(1 for h in sentinel if h.get("last_status") == "down")
        down_count += sum(1 for u in monitor if u.get("last_status") == "down")

        # ── Header ──────────────────────────────
        header = ft.Column([
            ft.Text("Dashboard", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            ft.Text(f"Último análisis: {ts}", size=12, color=T.TEXT_SECONDARY),
        ], spacing=2, tight=True)

        # ── Métricas ──────────────────────────
        metrics = ft.Row([
            T.metric_card("Descarga", dl, "Mbps"),
            T.metric_card("Subida", ul, "Mbps"),
            T.metric_card("Ping", ping, "ms"),
        ], spacing=10)

        # ── Alerta si hay hosts caídos ────────
        alerts = []
        if down_count > 0:
            alerts.append(T.alert_row(
                f"{down_count} host(s) caído(s) detectados — revisa Monitor / Sentinel",
                color=T.STATUS_DOWN
            ))
        if not last:
            alerts.append(T.alert_row(
                "Sin historial de velocidad. Ejecuta tu primer test desde la sección Speed Test.",
                color=T.LIME
            ))

        # ── Grid de herramientas ──────────────
        tools = [
            ("🏃", "Speed Test",         "Mide descarga, subida y latencia",    "speed"),
            ("📡", "Ping",               "Comprueba conectividad a un host",     "ping"),
            ("🔍", "Escáner de puertos", "Descubre puertos TCP abiertos",       "ports"),
            ("🌐", "DNS Lookup",         "Consulta registros DNS completos",    "dns"),
            ("🗺️", "Traceroute",         "Traza la ruta hasta el destino",     "traceroute"),
            ("📋", "Batch Ping",         "Ping masivo a lista de hosts",        "batch"),
            ("👁️", "Sentinel",           "Vigilancia continua de hosts",        "sentinel"),
            ("🔗", "Monitor URLs",       "Disponibilidad de servicios web",     "monitor"),
            ("📐", "Subnet Calc",        "Calculadora de subredes CIDR",        "subnet"),
            ("📖", "WHOIS",             "Consulta info de dominio",             "whois"),
        ]

        def make_tool_card(icon, name, desc, key):
            return ft.Container(
                content=ft.Column([
                    ft.Text(icon, size=22),
                    ft.Text(name, size=13, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                    ft.Text(desc, size=11, color=T.TEXT_SECONDARY),
                ], spacing=6, tight=True),
                bgcolor=T.DARK_SURFACE,
                border=ft.border.all(1, T.DARK_BORDER),
                border_radius=10,
                padding=14,
                on_click=lambda e, k=key: self.navigate(k),
                ink=True,
                expand=True,
            )

        grid_rows = []
        row_size = 3
        for i in range(0, len(tools), row_size):
            chunk = tools[i:i + row_size]
            grid_rows.append(ft.Row(
                [make_tool_card(*t) for t in chunk],
                spacing=10,
            ))

        self.controls = [
            header,
            metrics,
            *alerts,
            T.divider(),
            ft.Text("Herramientas", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            *grid_rows,
        ]

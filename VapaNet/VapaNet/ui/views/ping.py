"""
VapaNet — Vista Ping
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class PingView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._host_field = T.input_field("Host o IP", hint="google.com / 8.8.8.8")
        self._count_dd = T.dropdown_field("Paquetes", ["1", "2", "4", "8", "16"], value="4", width=110)
        self._timeout_dd = T.dropdown_field("Timeout (s)", ["1", "2", "3", "5"], value="2", width=130)
        self._run_btn = T.primary_button("Ping", on_click=self._run, icon=ft.icons.WIFI_TETHERING)
        self._output = ft.Text("", size=12, color=T.TEXT_PRIMARY, font_family="Consolas",
                               selectable=True)
        self._status_badge = ft.Container(visible=False)
        self._avg_text = ft.Text("", size=12, color=T.TEXT_MUTED)

        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("Ping", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Comprueba la conectividad y latencia a cualquier host", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._host_field, self._count_dd, self._timeout_dd], spacing=10),
                ft.Row([self._run_btn, self._status_badge, self._avg_text], spacing=12,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(
                    content=self._output,
                    bgcolor=T.DARK_BG,
                    border=ft.border.all(1, T.DARK_BORDER),
                    border_radius=8,
                    padding=12,
                    min_height=140,
                    visible=False,
                    ref=ft.Ref(),
                ),
            ], spacing=10), ref=self._get_output_container_ref()),

            T.divider(),
            ft.Text("Historial de pings", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]
        # Keep reference to output container
        self._out_container = self.controls[1].content.controls[2]

    def _get_output_container_ref(self):
        return None

    def _load_history(self):
        rows = db.get_ping_history(15)
        self._history_col.controls.clear()
        if not rows:
            self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
            return
        for r in rows:
            ts = r["timestamp"][:16].replace("T", " ")
            badge = T.status_badge(r["status"])
            self._history_col.controls.append(
                T.card(ft.Row([
                    ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                    ft.Text(r["host"], size=13, color=T.TEXT_PRIMARY, expand=True),
                    ft.Text(f"{r['avg_ms']:.1f} ms" if r["avg_ms"] else "—", size=13, color=T.LIME, width=80),
                    ft.Text(f"Pérdida: {r['packet_loss']:.0f}%", size=12, color=T.TEXT_SECONDARY, width=100),
                    badge,
                ], spacing=8))
            )

    def _run(self, e):
        host = self._host_field.value.strip()
        if not host:
            self._host_field.error_text = "Introduce un host"
            self.update()
            return
        self._host_field.error_text = None
        self._run_btn.disabled = True
        self._output.value = f"Haciendo ping a {host}…"
        self._out_container.visible = True
        self._status_badge.visible = False
        self._avg_text.value = ""
        self.update()

        count = int(self._count_dd.value or 4)
        timeout = int(self._timeout_dd.value or 2)

        def run():
            res = network.ping_host(host, count=count, timeout=timeout)
            self._output.value = res["raw"]
            self._status_badge.content = T.status_badge(res["status"])
            self._status_badge.visible = True
            self._avg_text.value = f"Media: {res['avg_ms']:.1f} ms | Pérdida: {res['packet_loss']:.0f}%"
            db.insert_ping_result(host, res["avg_ms"], res["packet_loss"], res["status"])
            self._load_history()
            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

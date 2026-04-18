"""
VapaNet — Vista Traceroute
"""

import flet as ft
import threading
from ui import theme as T
from core import network


class TracerouteView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._running = False
        self._build()

    def _build(self):
        self._host_field = T.input_field("Host o IP destino", hint="google.com / 1.1.1.1")
        self._maxhops_dd = T.dropdown_field("Máx saltos", ["10", "20", "30"], value="20", width=130)
        self._run_btn = T.primary_button("Trazar ruta", on_click=self._start, icon=ft.icons.ROUTE)
        self._stop_btn = T.secondary_button("Detener", on_click=self._stop)
        self._stop_btn.visible = False
        self._status_label = ft.Text("", size=12, color=T.TEXT_SECONDARY)
        self._hops_col = ft.Column(spacing=4)

        self.controls = [
            ft.Column([
                ft.Text("Traceroute", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Traza cada salto de red hasta el destino en tiempo real", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._host_field, self._maxhops_dd], spacing=10),
                ft.Row([self._run_btn, self._stop_btn, self._status_label], spacing=12,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=10)),

            T.card(ft.Column([
                ft.Row([
                    ft.Text("Salto", size=11, color=T.TEXT_MUTED, width=50),
                    ft.Text("IP / Host", size=11, color=T.TEXT_MUTED, expand=True),
                    ft.Text("Latencia", size=11, color=T.TEXT_MUTED, width=90),
                    ft.Text("Barra", size=11, color=T.TEXT_MUTED, width=120),
                ], spacing=0),
                T.divider(),
                self._hops_col,
            ], spacing=8)),
        ]

    def _start(self, e):
        host = self._host_field.value.strip()
        if not host:
            self._host_field.error_text = "Introduce un host"
            self.update()
            return
        self._host_field.error_text = None
        self._running = True
        self._hops_col.controls.clear()
        self._run_btn.visible = False
        self._stop_btn.visible = True
        self._status_label.value = f"Trazando ruta a {host}…"
        self.update()

        max_hops = int(self._maxhops_dd.value or 20)
        max_ms = [1]

        def on_hop(hop):
            if not self._running:
                return
            ms = hop.get("avg_ms")
            ms_str = f"{ms:.1f} ms" if ms else "*"

            # Bar proportional to latency
            if ms and ms > max_ms[0]:
                max_ms[0] = ms
            bar_w = int((ms / max_ms[0]) * 120) if ms and max_ms[0] > 0 else 4
            bar_color = T.STATUS_UP if ms and ms < 50 else (T.STATUS_WARN if ms and ms < 150 else T.STATUS_DOWN)

            row = ft.Row([
                ft.Text(str(hop["hop"]), size=13, color=T.LIME, width=50,
                        weight=ft.FontWeight.W_500),
                ft.Text(hop.get("ip", "*"), size=12, color=T.TEXT_PRIMARY,
                        font_family="Consolas", expand=True),
                ft.Text(ms_str, size=13, color=bar_color if ms else T.TEXT_MUTED, width=90),
                ft.Container(
                    width=max(4, bar_w),
                    height=6,
                    bgcolor=bar_color if ms else T.DARK_BORDER,
                    border_radius=3,
                ),
            ], spacing=0)
            self._hops_col.controls.append(row)
            try:
                self.update()
            except Exception:
                pass

        def run():
            network.traceroute(host, max_hops=max_hops, timeout=2, on_hop=on_hop)
            if self._running:
                self._status_label.value = f"✓ Ruta completa — {len(self._hops_col.controls)} saltos"
            self._running = False
            self._run_btn.visible = True
            self._stop_btn.visible = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    def _stop(self, e):
        self._running = False
        self._status_label.value = "Detenido"
        self._run_btn.visible = True
        self._stop_btn.visible = False
        self.update()

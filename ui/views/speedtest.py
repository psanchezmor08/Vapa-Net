"""
VapaNet — Vista Speed Test
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class SpeedTestView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._running = False
        self._build()

    def _build(self):
        self._phase_label = ft.Text("Listo para medir", size=13, color=T.TEXT_SECONDARY)
        self._progress = T.progress_bar(value=0)
        self._dl_val = ft.Text("—", size=40, weight=ft.FontWeight.W_500, color=T.LIME)
        self._ul_val = ft.Text("—", size=40, weight=ft.FontWeight.W_500, color=T.LIME)
        self._ping_val = ft.Text("—", size=40, weight=ft.FontWeight.W_500, color=T.LIME)
        self._server_label = ft.Text("", size=11, color=T.TEXT_MUTED)

        self._run_btn = T.primary_button("▶  Iniciar test", on_click=self._start, width=200)

        results_row = ft.Row([
            ft.Column([
                ft.Text("Descarga", size=11, color=T.TEXT_SECONDARY),
                self._dl_val,
                ft.Text("Mbps", size=12, color=T.TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ft.VerticalDivider(width=1, color=T.DARK_BORDER),
            ft.Column([
                ft.Text("Subida", size=11, color=T.TEXT_SECONDARY),
                self._ul_val,
                ft.Text("Mbps", size=12, color=T.TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ft.VerticalDivider(width=1, color=T.DARK_BORDER),
            ft.Column([
                ft.Text("Ping", size=11, color=T.TEXT_SECONDARY),
                self._ping_val,
                ft.Text("ms", size=12, color=T.TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
        ], expand=True)

        # Historial
        self._history_col = ft.Column(spacing=6)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("Speed Test", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Mide tu velocidad de conexión real", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                results_row,
                ft.Container(height=16),
                self._phase_label,
                self._progress,
                ft.Container(height=8),
                ft.Row([self._run_btn, self._server_label], spacing=16,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=8)),

            T.divider(),
            ft.Text("Historial reciente", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _load_history(self):
        rows = db.get_speed_history(10)
        self._history_col.controls.clear()
        if not rows:
            self._history_col.controls.append(
                ft.Text("Sin historial aún.", size=12, color=T.TEXT_MUTED)
            )
            return
        for r in rows:
            ts = r["timestamp"][:16].replace("T", " ")
            self._history_col.controls.append(
                T.card(ft.Row([
                    ft.Text(ts, size=12, color=T.TEXT_MUTED, width=130),
                    ft.Text(f"↓ {r['download_mbps']:.1f} Mbps", size=13, color=T.LIME, width=120),
                    ft.Text(f"↑ {r['upload_mbps']:.1f} Mbps", size=13, color=T.LIME, width=120),
                    ft.Text(f"Ping: {r['ping_ms']:.0f} ms", size=13, color=T.TEXT_SECONDARY),
                ], spacing=0))
            )

    def _start(self, e):
        if self._running:
            return
        self._running = True
        self._run_btn.disabled = True
        self._dl_val.value = "…"
        self._ul_val.value = "…"
        self._ping_val.value = "…"
        self._phase_label.value = "Iniciando…"
        self._progress.value = None
        self.update()

        def run():
            def on_progress(phase, pct):
                labels = {"ping": "Midiendo latencia…", "download": "Descargando…", "upload": "Subiendo…"}
                self._phase_label.value = labels.get(phase, phase)
                self._progress.value = pct / 100 if pct > 0 else None
                try:
                    self.update()
                except Exception:
                    pass

            try:
                res = network.speedtest_native(on_progress=on_progress)
                self._dl_val.value = f"{res['download_mbps']:.1f}"
                self._ul_val.value = f"{res['upload_mbps']:.1f}"
                self._ping_val.value = f"{res['ping_ms']:.0f}"
                self._server_label.value = res.get("server", "")
                self._phase_label.value = "✓ Test completado"
                self._progress.value = 1.0
                db.insert_speed_result(
                    res["download_mbps"], res["upload_mbps"],
                    res["ping_ms"], res.get("server", "")
                )
                self._load_history()
            except Exception as ex:
                self._phase_label.value = f"Error: {ex}"
                self._progress.value = 0
            finally:
                self._running = False
                self._run_btn.disabled = False
                try:
                    self.update()
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()

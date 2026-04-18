"""
VapaNet — Vista Batch Ping
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class BatchPingView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._running = False
        self._build()

    def _build(self):
        self._hosts_field = ft.TextField(
            label="Lista de hosts (uno por línea, # para comentarios)",
            hint_text="google.com\n8.8.8.8\n# servidor interno\n192.168.1.1",
            multiline=True,
            min_lines=6,
            max_lines=12,
            bgcolor=T.DARK_PANEL,
            border_color=T.DARK_BORDER,
            focused_border_color=T.LIME,
            label_style=ft.TextStyle(color=T.TEXT_SECONDARY, size=12),
            text_style=ft.TextStyle(color=T.TEXT_PRIMARY, size=13, font_family="Consolas"),
            border_radius=8,
            expand=True,
        )
        self._count_dd = T.dropdown_field("Paquetes", ["1", "2", "4"], value="2", width=110)
        self._run_btn = T.primary_button("Ejecutar Batch", on_click=self._start,
                                         icon=ft.Icons.PLAYLIST_PLAY)
        self._stop_btn = T.secondary_button("Detener", on_click=self._stop, icon=ft.Icons.STOP)
        self._stop_btn.visible = False
        self._progress = T.progress_bar(value=0)
        self._progress_label = ft.Text("", size=11, color=T.TEXT_MUTED)

        self._stats_row = ft.Row([], spacing=10)
        self._results_col = ft.Column(spacing=4)

        example_btn = ft.TextButton(
            "Cargar ejemplos",
            on_click=self._load_examples,
            style=ft.ButtonStyle(color=T.LIME_MUTED),
        )

        self.controls = [
            ft.Column([
                ft.Text("Batch Ping", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Envía ping a múltiples hosts simultáneamente", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([example_btn], spacing=0),
                self._hosts_field,
                ft.Row([self._count_dd, self._run_btn, self._stop_btn], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self._progress,
                self._progress_label,
            ], spacing=10)),

            self._stats_row,
            self._results_col,
        ]

    def _load_examples(self, e):
        self._hosts_field.value = (
            "# Servidores DNS públicos\n"
            "8.8.8.8\n"
            "8.8.4.4\n"
            "1.1.1.1\n"
            "1.0.0.1\n"
            "# Sitios web\n"
            "google.com\n"
            "cloudflare.com\n"
            "github.com\n"
        )
        self.update()

    def _start(self, e):
        raw = self._hosts_field.value or ""
        hosts = network.parse_hosts_file(raw)
        if not hosts:
            self._progress_label.value = "Sin hosts válidos en la lista"
            self.update()
            return

        self._running = True
        self._results_col.controls.clear()
        self._stats_row.controls.clear()
        self._run_btn.visible = False
        self._stop_btn.visible = True
        self._progress.value = None
        self._progress_label.value = f"Iniciando ping a {len(hosts)} hosts…"
        self.update()

        count = int(self._count_dd.value or 2)
        total = len(hosts)
        done = [0]
        up = [0]
        down = [0]

        def on_result(res):
            if not self._running:
                return
            done[0] += 1
            if res["status"] == "up":
                up[0] += 1
            else:
                down[0] += 1

            self._progress.value = done[0] / total
            self._progress_label.value = f"{done[0]}/{total} procesados — {up[0]} activos / {down[0]} caídos"

            badge = T.status_badge(res["status"])
            ms_str = f"{res['avg_ms']:.1f} ms" if res["avg_ms"] else "—"
            loss_str = f"{res['packet_loss']:.0f}% pérdida"

            row = T.card(ft.Row([
                ft.Text(res["host"], size=13, color=T.TEXT_PRIMARY, expand=True,
                        font_family="Consolas"),
                ft.Text(ms_str, size=13, color=T.LIME if res["status"] == "up" else T.TEXT_MUTED,
                        width=80),
                ft.Text(loss_str, size=12, color=T.TEXT_SECONDARY, width=100),
                badge,
            ], spacing=10))
            self._results_col.controls.append(row)
            try:
                self.update()
            except Exception:
                pass

        def run():
            all_res = network.batch_ping(hosts, count=count, timeout=1, on_result=on_result)
            self._stats_row.controls = [
                T.metric_card("Total", str(total)),
                T.metric_card("Activos", str(up[0])),
                T.metric_card("Caídos", str(down[0])),
                T.metric_card("Tasa UP", f"{int(up[0]/total*100)}%"),
            ]
            db.insert_batch_results("batch", [
                {"host": r["host"], "status": r["status"],
                 "avg_ms": r["avg_ms"], "loss": r["packet_loss"]} for r in all_res
            ])
            self._progress_label.value = f"✓ Completado — {up[0]}/{total} activos"
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
        self._progress_label.value = "Detenido"
        self._run_btn.visible = True
        self._stop_btn.visible = False
        self.update()

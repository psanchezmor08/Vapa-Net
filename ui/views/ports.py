"""
VapaNet — Vista Escáner de Puertos
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


PRESETS = {
    "Común (top 22)": "21,22,23,25,53,80,110,143,443,445,3306,3389,5432,5900,6379,8080,8443,27017,1433,5000,8888,9200",
    "Web": "80,443,8080,8443,3000,4000,5000,8000,8888,9000,9090",
    "Bases de datos": "3306,5432,27017,6379,1433,1521,5984,9200,7474",
    "Rango 1-1024": "1-1024",
    "Personalizado": "",
}


class PortScanView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._running = False
        self._results = []
        self._build()

    def _build(self):
        self._host_field = T.input_field("Host o IP", hint="192.168.1.1 / scanme.nmap.org")
        self._preset_dd = T.dropdown_field("Preset", list(PRESETS.keys()),
                                           value="Común (top 22)", on_change=self._on_preset, width=200)  # on_change mapped to on_select in theme
        self._ports_field = T.input_field("Puertos", hint="22,80,443 / 8000-9000",
                                          value=PRESETS["Común (top 22)"])
        self._timeout_dd = T.dropdown_field("Timeout (s)", ["0.3", "0.5", "1", "2"],
                                            value="0.5", width=130)
        self._run_btn = T.primary_button("Escanear", on_click=self._start, icon=ft.Icons.RADAR)
        self._stop_btn = T.secondary_button("Detener", on_click=self._stop, icon=ft.Icons.STOP)
        self._stop_btn.visible = False

        self._progress = T.progress_bar(value=0)
        self._progress_label = ft.Text("", size=11, color=T.TEXT_MUTED)
        self._stats_row = ft.Row([], spacing=16)
        self._results_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

        self.controls = [
            ft.Column([
                ft.Text("Escáner de Puertos", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Descubre puertos TCP abiertos en cualquier host", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._host_field, self._preset_dd], spacing=10),
                ft.Row([self._ports_field, self._timeout_dd], spacing=10),
                ft.Row([self._run_btn, self._stop_btn, self._progress_label], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self._progress,
            ], spacing=10)),

            self._stats_row,
            self._results_col,
        ]

    def _on_preset(self, e):
        val = PRESETS.get(self._preset_dd.value, "")
        if val:
            self._ports_field.value = val
        self.update()

    def _start(self, e):
        host = self._host_field.value.strip()
        if not host:
            self._host_field.error_text = "Introduce un host"
            self.update()
            return
        ports_str = self._ports_field.value.strip()
        if not ports_str:
            self._ports_field.error_text = "Define los puertos"
            self.update()
            return
        self._host_field.error_text = None
        self._ports_field.error_text = None

        ports = network.parse_port_range(ports_str)
        if not ports:
            self._progress_label.value = "Sin puertos válidos"
            self.update()
            return

        self._running = True
        self._results = []
        self._results_col.controls.clear()
        self._stats_row.controls.clear()
        self._run_btn.visible = False
        self._stop_btn.visible = True
        self._progress.value = None
        self._progress_label.value = f"Escaneando {len(ports)} puertos en {host}…"
        self.update()

        timeout = float(self._timeout_dd.value or 0.5)
        total = len(ports)
        done = [0]

        def on_result(res):
            if not self._running:
                return
            done[0] += 1
            self._progress.value = done[0] / total
            if res["status"] == "open":
                self._results.append(res)
                self._add_result_row(res)
            if done[0] % 20 == 0:
                self._progress_label.value = f"{done[0]}/{total} puertos analizados…"
                try:
                    self.update()
                except Exception:
                    pass

        def run():
            all_results = network.scan_ports(host, ports, timeout=timeout, on_result=on_result)
            open_count = sum(1 for r in all_results if r["status"] == "open")
            self._progress.value = 1.0
            self._progress_label.value = f"✓ Completado — {open_count} abiertos / {total} escaneados"
            self._stats_row.controls = [
                T.metric_card("Total escaneados", str(total)),
                T.metric_card("Abiertos", str(open_count), trend="TCP"),
                T.metric_card("Cerrados", str(total - open_count)),
            ]
            if open_count == 0:
                self._results_col.controls.append(
                    ft.Text("No se encontraron puertos abiertos.", size=12, color=T.TEXT_MUTED)
                )
            db.insert_port_scan(host, all_results)
            self._running = False
            self._run_btn.visible = True
            self._stop_btn.visible = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

    def _add_result_row(self, res):
        service = res.get("service", "")
        self._results_col.controls.append(
            T.card(ft.Row([
                ft.Text(str(res["port"]), size=14, weight=ft.FontWeight.W_500,
                        color=T.LIME, width=70),
                T.status_badge("open"),
                ft.Text(service if service else "desconocido", size=13,
                        color=T.TEXT_SECONDARY, expand=True),
            ], spacing=12))
        )

    def _stop(self, e):
        self._running = False
        self._progress_label.value = "Detenido por el usuario"
        self._run_btn.visible = True
        self._stop_btn.visible = False
        self.update()

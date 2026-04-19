"""
VapaNet — Vista Reverse DNS Lookup
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class ReverseDNSView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._ip_field = T.input_field("Dirección IP", hint="8.8.8.8")
        self._run_btn = T.primary_button("Buscar Hostname", on_click=self._run, icon=ft.Icons.LANGUAGE)
        self._info_col = ft.Column(spacing=10)
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("Reverse DNS Lookup", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Encuentra el nombre de dominio (hostname) para una dirección IP", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._ip_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            self._info_col,

            T.divider(),
            ft.Text("Historial de búsquedas", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _load_history(self):
        try:
            rows = db.get_reverse_dns_history(15)
            self._history_col.controls.clear()
            if not rows:
                self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
                return
            for r in rows:
                ts = r["timestamp"][:16].replace("T", " ")
                hostname = r["hostname"] if r["hostname"] else "No resuelto"
                self._history_col.controls.append(
                    T.card(ft.Row([
                        ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                        ft.Text(r["ip"], size=12, color=T.TEXT_PRIMARY, width=130, font_family="Consolas"),
                        ft.Text(hostname, size=12, color=T.TEXT_SECONDARY, expand=True),
                    ], spacing=8))
                )
        except Exception:
            self._history_col.controls.clear()
            self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))

    def _run(self, e):
        ip = self._ip_field.value.strip()
        if not ip:
            self._ip_field.error_text = "Introduce una IP"
            self.update()
            return
        self._ip_field.error_text = None
        self._run_btn.disabled = True
        self._info_col.controls = [T.progress_bar()]
        self.update()

        def run():
            res = network.reverse_dns(ip)
            self._info_col.controls.clear()

            if not res['valid']:
                self._info_col.controls.append(
                    T.alert_row(f"⚠️ {res['error']}", color=T.STATUS_WARN)
                )
                db.insert_reverse_dns_result(ip, "No resuelto", res['response_ms'])
            else:
                self._info_col.controls.append(
                    T.card(ft.Column([
                        ft.Row([
                            ft.Text("Hostname", size=12, color=T.TEXT_SECONDARY, width=120),
                            ft.Text(res['hostname'], size=13, color=T.TEXT_PRIMARY, expand=True, font_family="Consolas"),
                        ]),
                        ft.Row([
                            ft.Text("Aliases", size=12, color=T.TEXT_SECONDARY, width=120),
                            ft.Text(res['aliases'], size=12, color=T.TEXT_SECONDARY),
                        ]),
                        ft.Row([
                            ft.Text("Direcciones", size=12, color=T.TEXT_SECONDARY, width=120),
                            ft.Text(res['addresses'], size=12, color=T.TEXT_SECONDARY),
                        ]),
                        ft.Text(f"Tiempo: {res['response_ms']:.0f} ms", size=10, color=T.TEXT_MUTED),
                    ], spacing=10))
                )
                db.insert_reverse_dns_result(ip, res['hostname'], res['response_ms'])

            self._load_history()
            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

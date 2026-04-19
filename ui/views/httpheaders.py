"""
VapaNet — Vista HTTP Header Analyzer
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class HTTPHeadersView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._url_field = T.input_field("URL", hint="ejemplo.com o https://ejemplo.com")
        self._run_btn = T.primary_button("Analizar Headers", on_click=self._run, icon=ft.Icons.HTTP)
        self._info_col = ft.Column(spacing=10)
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("HTTP Header Analyzer", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Examina los headers HTTP/HTTPS de un sitio web", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._url_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            self._info_col,

            T.divider(),
            ft.Text("Historial de análisis", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _load_history(self):
        try:
            rows = db.get_http_headers_history(15)
            self._history_col.controls.clear()
            if not rows:
                self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
                return
            for r in rows:
                ts = r["timestamp"][:16].replace("T", " ")
                status_color = T.STATUS_UP if 200 <= r["status_code"] < 300 else (T.STATUS_WARN if 300 <= r["status_code"] < 400 else T.STATUS_DOWN)
                self._history_col.controls.append(
                    T.card(ft.Row([
                        ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                        ft.Text(r["url"][:40], size=12, color=T.TEXT_PRIMARY, expand=True),
                        ft.Container(
                            content=ft.Text(f"{r['status_code']}", size=11, color=T.TEXT_PRIMARY),
                            bgcolor=status_color,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            width=50,
                        ),
                    ], spacing=8))
                )
        except Exception:
            self._history_col.controls.clear()
            self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))

    def _run(self, e):
        url = self._url_field.value.strip()
        if not url:
            self._url_field.error_text = "Introduce una URL"
            self.update()
            return
        self._url_field.error_text = None
        self._run_btn.disabled = True
        self._info_col.controls = [T.progress_bar()]
        self.update()

        def run():
            res = network.get_http_headers(url)
            self._info_col.controls.clear()

            if not res['valid']:
                self._info_col.controls.append(
                    T.alert_row(f"Error: {res['error']}", color=T.STATUS_WARN)
                )
            else:
                status_color = T.STATUS_UP if 200 <= res['status_code'] < 300 else (T.STATUS_WARN if 300 <= res['status_code'] < 400 else T.STATUS_DOWN)
                self._info_col.controls.append(
                    T.card(ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"Status {res['status_code']}", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                                ft.Text(res['status_text'], size=11, color=T.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(f"{res['status_code']}", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                                bgcolor=status_color,
                                border_radius=6,
                                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                            ),
                        ]),
                        ft.Text(f"Tiempo: {res['response_ms']:.0f} ms", size=11, color=T.TEXT_MUTED),
                    ], spacing=8))
                )

                # Headers
                if res['headers']:
                    headers_controls = []
                    important_headers = ['server', 'content-type', 'content-length', 'cache-control', 'set-cookie', 'x-frame-options', 'strict-transport-security', 'x-content-type-options']
                    
                    for header, value in res['headers'].items():
                        if header.lower() in important_headers:
                            headers_controls.append(ft.Row([
                                ft.Text(header, size=11, color=T.LIME, width=200, weight=ft.FontWeight.W_500),
                                ft.Text(str(value)[:100], size=11, color=T.TEXT_PRIMARY, expand=True),
                            ]))
                    
                    if headers_controls:
                        self._info_col.controls.append(T.card(ft.Column(headers_controls, spacing=8)))

                server = res['headers'].get('server', 'Unknown')
                content_type = res['headers'].get('content-type', 'Unknown')
                db.insert_http_headers_result(url, res['status_code'], server, content_type, res['response_ms'])
                self._load_history()

            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

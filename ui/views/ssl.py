"""
VapaNet — Vista SSL/TLS Certificate Info
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class SSLView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._domain_field = T.input_field("Dominio", hint="ejemplo.com")
        self._run_btn = T.primary_button("Verificar SSL", on_click=self._run, icon=ft.Icons.VERIFIED_USER)
        self._status_label = ft.Text("", size=12, color=T.TEXT_MUTED)
        self._info_col = ft.Column(spacing=10)
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("SSL/TLS Certificate Info", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Verifica validez y detalles del certificado SSL de un dominio", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._domain_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            ft.Container(
                content=self._status_label,
                visible=False,
                ref=ft.Ref(),
            ),

            self._info_col,

            T.divider(),
            ft.Text("Historial de verificaciones", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]
        self._status_container = self.controls[2]

    def _load_history(self):
        try:
            rows = db.get_ssl_history(15)
            self._history_col.controls.clear()
            if not rows:
                self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
                return
            for r in rows:
                ts = r["timestamp"][:16].replace("T", " ")
                status_icon = "✓" if not r["is_expired"] else "✗"
                status_color = T.STATUS_UP if not r["is_expired"] else T.STATUS_DOWN
                self._history_col.controls.append(
                    T.card(ft.Row([
                        ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                        ft.Text(r["domain"], size=13, color=T.TEXT_PRIMARY, expand=True),
                        ft.Text(status_icon, size=16, color=status_color, width=30),
                        ft.Text(f"{r['days_until_expiry']}d", size=12, color=T.TEXT_SECONDARY, width=50),
                    ], spacing=8))
                )
        except Exception:
            self._history_col.controls.clear()
            self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))

    def _run(self, e):
        domain = self._domain_field.value.strip()
        if not domain:
            self._domain_field.error_text = "Introduce un dominio"
            self.update()
            return
        self._domain_field.error_text = None
        self._run_btn.disabled = True
        self._info_col.controls = [T.progress_bar()]
        self._status_container.visible = False
        self.update()

        def run():
            res = network.get_ssl_info(domain)
            self._info_col.controls.clear()

            if not res['valid']:
                self._info_col.controls.append(
                    T.alert_row(f"Error: {res['error']}", color=T.STATUS_DOWN)
                )
            else:
                # Main info
                warning_color = T.STATUS_DOWN if res['is_expired'] else (T.STATUS_WARN if res['days_until_expiry'] < 30 else T.STATUS_UP)
                self._info_col.controls.append(
                    T.card(ft.Column([
                        ft.Row([
                            ft.Text(res['cn'], size=16, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY, expand=True),
                            ft.Container(
                                content=ft.Text(res['warning'], size=11, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                                bgcolor=warning_color,
                                border_radius=5,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ]),
                        ft.Text(res['issuer'], size=12, color=T.TEXT_SECONDARY),
                        ft.Text(f"Válido desde: {res['valid_from']}", size=11, color=T.TEXT_MUTED),
                        ft.Text(f"Válido hasta: {res['valid_to']}", size=11, color=T.TEXT_MUTED),
                        ft.Text(f"Caduca en: {res['days_until_expiry']} días", size=12, color=warning_color, weight=ft.FontWeight.W_500),
                    ], spacing=8))
                )

                # Details
                details = []
                details.append(ft.Row([
                    ft.Text("Algoritmo:", size=12, color=T.TEXT_SECONDARY, width=120),
                    ft.Text(res['version'], size=12, color=T.TEXT_PRIMARY),
                ]))
                details.append(ft.Row([
                    ft.Text("Serial:", size=12, color=T.TEXT_SECONDARY, width=120),
                    ft.Text(res['serial'], size=12, color=T.TEXT_PRIMARY, font_family="Consolas"),
                ]))
                if res['san'] != 'None':
                    details.append(ft.Row([
                        ft.Text("SANs:", size=12, color=T.TEXT_SECONDARY, width=120),
                        ft.Text(res['san'], size=11, color=T.TEXT_PRIMARY),
                    ]))

                self._info_col.controls.append(T.card(ft.Column(details, spacing=10)))

                db.insert_ssl_result(domain, res['cn'], res['issued_by'], res['valid_from'], 
                                   res['valid_to'], res['days_until_expiry'], int(res['is_expired']), res['response_ms'])
                self._load_history()

            self._status_label.value = f"Tiempo de respuesta: {res['response_ms']:.0f} ms"
            self._status_container.visible = True
            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

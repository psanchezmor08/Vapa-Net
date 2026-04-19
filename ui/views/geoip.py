"""
VapaNet — Vista Geoip Lookup
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class GeoIPView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._ip_field = T.input_field("Dirección IP", hint="8.8.8.8")
        self._run_btn = T.primary_button("Localizar IP", on_click=self._run, icon=ft.Icons.PUBLIC)
        self._map_url = ft.Text("", size=11, color=T.LIME)
        self._info_col = ft.Column(spacing=10)
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("Geoip Lookup", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Localiza geográficamente una dirección IP", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._ip_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            ft.Column([
                ft.Text("Ver en mapa:", size=11, color=T.TEXT_MUTED),
                self._map_url,
            ], spacing=4),

            self._info_col,

            T.divider(),
            ft.Text("Historial de búsquedas", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _load_history(self):
        try:
            rows = db.get_geoip_history(15)
            self._history_col.controls.clear()
            if not rows:
                self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
                return
            for r in rows:
                ts = r["timestamp"][:16].replace("T", " ")
                self._history_col.controls.append(
                    T.card(ft.Row([
                        ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                        ft.Text(r["ip"], size=12, color=T.TEXT_PRIMARY, width=130, font_family="Consolas"),
                        ft.Text(f"{r['country']}", size=12, color=T.TEXT_SECONDARY, expand=True),
                        ft.Text(f"{r['city']}" if r['city'] else "-", size=12, color=T.TEXT_MUTED, width=100),
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
        self._map_url.value = ""
        self.update()

        def run():
            res = network.geoip_lookup(ip)
            self._info_col.controls.clear()

            if not res['valid']:
                self._info_col.controls.append(
                    T.alert_row(f"Error: {res['error']}", color=T.STATUS_WARN)
                )
            else:
                # Location card
                self._info_col.controls.append(
                    T.card(ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text(f"{res['city']}" if res['city'] != 'N/A' else 'Desconocida', size=16, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                                ft.Text(f"{res['region']}, {res['country']}", size=12, color=T.TEXT_SECONDARY),
                            ], spacing=2, expand=True),
                            ft.Container(
                                content=ft.Text(f"🌍 {res['country']}", size=12, weight=ft.FontWeight.W_500, color=T.DARK_BG),
                                bgcolor=T.LIME,
                                border_radius=5,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ]),
                    ], spacing=8))
                )

                # Map URL
                if res['latitude'] != 'N/A':
                    map_url = f"https://maps.google.com/?q={res['latitude']},{res['longitude']}"
                    self._map_url.value = map_url

                # Details
                details = []
                if res['latitude'] != 'N/A':
                    details.append(ft.Row([
                        ft.Text("Coordenadas:", size=12, color=T.TEXT_SECONDARY, width=140),
                        ft.Text(res['coordinates'], size=12, color=T.TEXT_PRIMARY),
                    ]))
                if res['isp'] != 'N/A':
                    details.append(ft.Row([
                        ft.Text("ISP:", size=12, color=T.TEXT_SECONDARY, width=140),
                        ft.Text(res['isp'], size=12, color=T.TEXT_PRIMARY),
                    ]))
                if res['org'] != 'N/A':
                    details.append(ft.Row([
                        ft.Text("Organización:", size=12, color=T.TEXT_SECONDARY, width=140),
                        ft.Text(res['org'], size=12, color=T.TEXT_PRIMARY),
                    ]))
                if res['asn'] != 'N/A':
                    details.append(ft.Row([
                        ft.Text("ASN:", size=12, color=T.TEXT_SECONDARY, width=140),
                        ft.Text(res['asn'], size=12, color=T.TEXT_PRIMARY),
                    ]))

                if details:
                    self._info_col.controls.append(T.card(ft.Column(details, spacing=10)))

                db.insert_geoip_result(ip, res['country'], res['region'], res['city'],
                                      res['latitude'], res['longitude'], res['isp'], res['response_ms'])
                self._load_history()

            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

"""
VapaNet — Vista Calculadora de Subredes
"""

import flet as ft
from ui import theme as T
from core import network


class SubnetView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._cidr_field = T.input_field(
            "CIDR o IP con máscara",
            hint="192.168.1.0/24  ó  10.0.0.0 255.0.0.0"
        )
        self._run_btn = T.primary_button("Calcular", on_click=self._calc, icon=ft.Icons.CALCULATE)

        presets = [
            ("/8 — Clase A", "10.0.0.0/8"),
            ("/16 — Clase B", "172.16.0.0/16"),
            ("/24 — Clase C", "192.168.1.0/24"),
            ("/25 — Media C", "192.168.1.0/25"),
            ("/30 — P2P", "10.10.10.0/30"),
        ]
        preset_row = ft.Row([
            ft.TextButton(
                label,
                on_click=lambda e, v=val: self._set_preset(v),
                style=ft.ButtonStyle(color=T.LIME_MUTED),
            )
            for label, val in presets
        ], wrap=True, spacing=4)

        self._result_col = ft.Column(spacing=10)

        self.controls = [
            ft.Column([
                ft.Text("Subnet Calculator", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Calcula todos los parámetros de una subred CIDR", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._cidr_field, self._run_btn], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.END),
                ft.Row([ft.Text("Ejemplos rápidos:", size=11, color=T.TEXT_MUTED), preset_row],
                       spacing=8, wrap=True),
            ], spacing=10)),

            self._result_col,
        ]

    def _set_preset(self, val):
        self._cidr_field.value = val
        self._calc(None)

    def _calc(self, e):
        cidr = self._cidr_field.value.strip()
        if not cidr:
            self._cidr_field.error_text = "Introduce un CIDR"
            self.update()
            return
        self._cidr_field.error_text = None
        res = network.subnet_calc(cidr)

        self._result_col.controls.clear()

        if res.get("error"):
            self._result_col.controls.append(
                T.alert_row(f"Error: {res['error']}", color=T.STATUS_DOWN)
            )
            self.update()
            return

        metrics = ft.Row([
            T.metric_card("Red", res["network"]),
            T.metric_card("Broadcast", res["broadcast"]),
            T.metric_card("Hosts válidos", f"{res['total_hosts']:,}"),
        ], spacing=10)

        def info_row(label, val, mono=True):
            return ft.Row([
                ft.Text(label, size=12, color=T.TEXT_SECONDARY, width=180),
                ft.Text(
                    str(val), size=13, color=T.TEXT_PRIMARY,
                    font_family="Consolas" if mono else None,
                    selectable=True, expand=True,
                ),
            ], spacing=0)

        details = T.card(ft.Column([
            info_row("Dirección de red",    res["network"]),
            info_row("Broadcast",           res["broadcast"]),
            info_row("Máscara",             res["mask"]),
            info_row("Wildcard",            res["wildcard"]),
            info_row("Prefijo",             f"/{res['prefix']}"),
            info_row("Primer host",         res["first_host"]),
            info_row("Último host",         res["last_host"]),
            info_row("Total hosts",         f"{res['total_hosts']:,}"),
            info_row("Bits de host",        res["host_bits"]),
            info_row("Clase IP",            res["ip_class"], mono=False),
            info_row("¿IP privada?",        "Sí" if res["is_private"] else "No", mono=False),
        ], spacing=8))

        binary = T.card(ft.Column([
            ft.Text("Representación binaria", size=12, color=T.TEXT_MUTED),
            ft.Container(height=4),
            ft.Row([
                ft.Text("Red:", size=11, color=T.TEXT_SECONDARY, width=80),
                ft.Text(res["binary_network"], size=11, color=T.LIME,
                        font_family="Consolas", selectable=True),
            ]),
            ft.Row([
                ft.Text("Máscara:", size=11, color=T.TEXT_SECONDARY, width=80),
                ft.Text(res["binary_mask"], size=11, color=T.LIME_MUTED,
                        font_family="Consolas", selectable=True),
            ]),
        ], spacing=6))

        self._result_col.controls += [metrics, details, binary]
        self.update()

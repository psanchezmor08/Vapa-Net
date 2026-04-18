"""
VapaNet — Vista DNS Lookup
"""

import flet as ft
import threading
from ui import theme as T
from core import db, network


class DNSView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._domain_field = T.input_field("Dominio", hint="google.com / anthropic.com")
        self._type_dd = T.dropdown_field("Tipo de registro",
                                         network.COMMON_RECORD_TYPES, value="A", width=140)
        self._run_btn = T.primary_button("Consultar", on_click=self._run, icon=ft.icons.SEARCH)
        self._results_col = ft.Column(spacing=8)
        self._raw_text = ft.Text("", size=11, color=T.TEXT_MUTED, font_family="Consolas",
                                 selectable=True)
        self._raw_container = ft.Container(
            content=self._raw_text,
            bgcolor=T.DARK_BG,
            border=ft.border.all(1, T.DARK_BORDER),
            border_radius=8,
            padding=12,
            visible=False,
        )
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        # Quick lookup buttons
        quick = ft.Row([
            ft.TextButton("A", on_click=lambda e: self._quick("A")),
            ft.TextButton("AAAA", on_click=lambda e: self._quick("AAAA")),
            ft.TextButton("MX", on_click=lambda e: self._quick("MX")),
            ft.TextButton("NS", on_click=lambda e: self._quick("NS")),
            ft.TextButton("TXT", on_click=lambda e: self._quick("TXT")),
            ft.TextButton("CNAME", on_click=lambda e: self._quick("CNAME")),
        ], spacing=4)

        self.controls = [
            ft.Column([
                ft.Text("DNS Lookup", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Consulta registros DNS de cualquier dominio", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._domain_field, self._type_dd, self._run_btn], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.END),
                ft.Row([ft.Text("Acceso rápido:", size=11, color=T.TEXT_MUTED), quick], spacing=8),
            ], spacing=10)),

            self._results_col,
            self._raw_container,
            T.divider(),
            ft.Text("Historial DNS", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _quick(self, rtype):
        self._type_dd.value = rtype
        self._run(None)

    def _load_history(self):
        rows = db.get_dns_history(12)
        self._history_col.controls.clear()
        if not rows:
            self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
            return
        for r in rows:
            ts = r["timestamp"][:16].replace("T", " ")
            self._history_col.controls.append(
                T.card(ft.Row([
                    ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                    ft.Container(
                        content=ft.Text(r["record_type"], size=10, color=T.DARK_BG,
                                        weight=ft.FontWeight.W_500),
                        bgcolor=T.LIME,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        width=50,
                    ),
                    ft.Text(r["domain"], size=13, color=T.TEXT_PRIMARY, width=160),
                    ft.Text(r["result"][:60] + ("…" if len(r["result"]) > 60 else ""),
                            size=12, color=T.TEXT_SECONDARY, expand=True),
                    ft.Text(f"{r['resolve_ms']:.0f} ms", size=11, color=T.TEXT_MUTED),
                ], spacing=10))
            )

    def _run(self, e):
        domain = self._domain_field.value.strip()
        if not domain:
            self._domain_field.error_text = "Introduce un dominio"
            self.update()
            return
        self._domain_field.error_text = None
        self._run_btn.disabled = True
        self._results_col.controls = [T.progress_bar()]
        self._raw_container.visible = False
        self.update()

        rtype = self._type_dd.value or "A"

        def run():
            res = network.dns_lookup(domain, rtype)
            self._results_col.controls.clear()

            # Stats card
            ms_text = f"{res['resolve_ms']:.0f} ms"
            self._results_col.controls.append(
                ft.Row([
                    T.metric_card("Registros", str(len(res["result"]))),
                    T.metric_card("Tiempo", ms_text),
                    T.metric_card("Estado", "OK" if res["success"] else "Error"),
                ], spacing=10)
            )

            if res["result"]:
                for record in res["result"]:
                    self._results_col.controls.append(
                        T.lime_card(ft.Row([
                            ft.Container(
                                content=ft.Text(rtype, size=10, color=T.DARK_BG,
                                                weight=ft.FontWeight.W_500),
                                bgcolor=T.LIME,
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            ),
                            ft.Text(record, size=13, color=T.TEXT_PRIMARY,
                                    selectable=True, expand=True, font_family="Consolas"),
                        ], spacing=12))
                    )
                db.insert_dns_result(domain, rtype, " | ".join(res["result"]), res["resolve_ms"])
                self._load_history()
            else:
                self._results_col.controls.append(
                    T.alert_row(f"Sin registros {rtype} para {domain}", color=T.STATUS_WARN)
                )

            self._raw_text.value = res["raw"]
            self._raw_container.visible = True
            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

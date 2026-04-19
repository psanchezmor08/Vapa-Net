"""
VapaNet — Vista DNS Propagation Checker
"""

import flet as ft
import threading
import json
from ui import theme as T
from core import db, network


class DNSPropView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._domain_field = T.input_field("Dominio", hint="ejemplo.com")
        self._run_btn = T.primary_button("Verificar Propagación", on_click=self._run, icon=ft.Icons.PUBLIC)
        self._results_col = ft.Column(spacing=10)
        self._history_col = ft.Column(spacing=5)
        self._load_history()

        self.controls = [
            ft.Column([
                ft.Text("DNS Propagation Checker", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Verifica propagación de DNS en servidores públicos globales", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._domain_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            self._results_col,

            T.divider(),
            ft.Text("Historial de verificaciones", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._history_col,
        ]

    def _load_history(self):
        try:
            rows = db.get_dns_propagation_history(10)
            self._history_col.controls.clear()
            if not rows:
                self._history_col.controls.append(ft.Text("Sin historial.", size=12, color=T.TEXT_MUTED))
                return
            for r in rows:
                ts = r["timestamp"][:16].replace("T", " ")
                status = "✓ Propagado" if r["propagated"] else "✗ No propagado"
                color = T.STATUS_UP if r["propagated"] else T.STATUS_DOWN
                self._history_col.controls.append(
                    T.card(ft.Row([
                        ft.Text(ts, size=11, color=T.TEXT_MUTED, width=120),
                        ft.Text(r["domain"], size=13, color=T.TEXT_PRIMARY, expand=True),
                        ft.Container(
                            content=ft.Text(status, size=11, color=T.TEXT_PRIMARY),
                            bgcolor=color,
                            border_radius=4,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        ),
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
        self._results_col.controls = [T.progress_bar()]
        self.update()

        def run():
            res = network.check_dns_propagation(domain)
            self._results_col.controls.clear()

            # Summary
            all_propagated = all(r['status'] == 'Propagated' for r in res['results'].values())
            summary_color = T.STATUS_UP if all_propagated else T.STATUS_WARN
            summary_text = "✓ DNS completamente propagado" if all_propagated else "⚠️ Propagación incompleta"

            self._results_col.controls.append(
                T.card(ft.Column([
                    ft.Row([
                        ft.Text(summary_text, size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY, expand=True),
                        ft.Container(
                            content=ft.Text(f"{sum(1 for r in res['results'].values() if r['status'] == 'Propagated')}/{len(res['results'])}", size=12, color=T.TEXT_PRIMARY),
                            bgcolor=summary_color,
                            border_radius=6,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        ),
                    ]),
                ], spacing=8))
            )

            # Server results
            for name, result in res['results'].items():
                status_ok = result['status'] == 'Propagated'
                status_color = T.STATUS_UP if status_ok else T.STATUS_DOWN if 'Error' not in result['status'] else T.STATUS_WARN
                
                self._results_col.controls.append(
                    T.card(ft.Column([
                        ft.Row([
                            ft.Text(name, size=13, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY, expand=True),
                            ft.Container(
                                content=ft.Text("✓" if status_ok else "✗", size=14, color=T.TEXT_PRIMARY),
                                bgcolor=status_color,
                                border_radius=4,
                                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ]),
                        ft.Text(result['server'], size=11, color=T.TEXT_MUTED, font_family="Consolas"),
                        ft.Text(f"IP resuelta: {result['resolved_ip']}", size=12, color=T.TEXT_PRIMARY),
                        ft.Text(f"Tiempo: {result['response_ms']:.0f} ms", size=10, color=T.TEXT_MUTED),
                    ], spacing=6))
                )

            db.insert_dns_propagation_result(domain, int(all_propagated), json.dumps(res['results']))
            self._load_history()

            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()

"""
VapaNet — Vista WHOIS
"""

import flet as ft
import threading
from ui import theme as T
from core import network


class WhoisView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._build()

    def _build(self):
        self._domain_field = T.input_field("Dominio", hint="google.com / anthropic.com")
        self._run_btn = T.primary_button("Consultar WHOIS", on_click=self._run,
                                         icon=ft.icons.INFO_OUTLINE)
        self._status_label = ft.Text("", size=12, color=T.TEXT_MUTED)
        self._raw_text = ft.Text("", size=12, color=T.TEXT_PRIMARY,
                                 font_family="Consolas", selectable=True)
        self._raw_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Resultado WHOIS", size=12, color=T.TEXT_SECONDARY, expand=True),
                    self._status_label,
                ]),
                ft.Container(
                    content=self._raw_text,
                    bgcolor=T.DARK_BG,
                    border=ft.border.all(1, T.DARK_BORDER),
                    border_radius=8,
                    padding=14,
                ),
            ], spacing=8),
            visible=False,
        )
        self._parsed_col = ft.Column(spacing=8)

        self.controls = [
            ft.Column([
                ft.Text("WHOIS", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Consulta el registro de propietario de cualquier dominio", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Row([self._domain_field, self._run_btn], spacing=10,
                          vertical_alignment=ft.CrossAxisAlignment.END)),

            self._parsed_col,
            self._raw_container,
        ]

    def _run(self, e):
        domain = self._domain_field.value.strip()
        if not domain:
            self._domain_field.error_text = "Introduce un dominio"
            self.update()
            return
        self._domain_field.error_text = None
        self._run_btn.disabled = True
        self._parsed_col.controls = [T.progress_bar()]
        self._raw_container.visible = False
        self.update()

        def run():
            res = network.whois_lookup(domain)
            self._parsed_col.controls.clear()

            self._status_label.value = (
                f"Servidor: {res['server']} · {res['ms']:.0f} ms"
            )

            if res["success"]:
                # Parse key fields from raw
                parsed = _parse_whois_fields(res["raw"])
                if parsed:
                    rows = []
                    for k, v in parsed.items():
                        rows.append(ft.Row([
                            ft.Text(k, size=12, color=T.TEXT_SECONDARY, width=180),
                            ft.Text(v, size=13, color=T.TEXT_PRIMARY, selectable=True, expand=True),
                        ]))
                    self._parsed_col.controls.append(
                        T.card(ft.Column(rows, spacing=8))
                    )
            else:
                self._parsed_col.controls.append(
                    T.alert_row(f"Error consultando WHOIS: {res['raw'][:200]}", color=T.STATUS_WARN)
                )

            self._raw_text.value = res["raw"][:6000]
            self._raw_container.visible = True
            self._run_btn.disabled = False
            try:
                self.update()
            except Exception:
                pass

        threading.Thread(target=run, daemon=True).start()


def _parse_whois_fields(raw: str) -> dict:
    import re
    fields_map = {
        "Domain Name":      r"Domain Name:\s*(.+)",
        "Registrar":        r"Registrar:\s*(.+)",
        "Registrant Org":   r"Registrant Organization:\s*(.+)",
        "Registrant Email": r"Registrant Email:\s*(.+)",
        "Creation Date":    r"Creation Date:\s*(.+)",
        "Updated Date":     r"Updated Date:\s*(.+)",
        "Expiry Date":      r"(?:Registrar )?Expir(?:y|ation) Date:\s*(.+)",
        "Name Servers":     r"Name Server:\s*(.+)",
        "Status":           r"Domain Status:\s*(.+)",
        "Country":          r"Registrant Country:\s*(.+)",
    }
    result = {}
    for label, pattern in fields_map.items():
        m = re.search(pattern, raw, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val and label not in result:
                result[label] = val[:120]
    return result

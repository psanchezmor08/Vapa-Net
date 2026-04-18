"""
VapaNet — Vista Monitor de URLs
"""

import flet as ft
import threading
import time
from ui import theme as T
from core import db, network


class MonitorView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._monitoring = False
        self._build()

    def _build(self):
        self._url_field = T.input_field("URL", hint="https://ejemplo.com / mi-servidor.local", expand=True)
        self._alias_field = T.input_field("Alias (opcional)", hint="Portal clientes", expand=True)
        self._add_btn = T.primary_button("Añadir", on_click=self._add_url, icon=ft.icons.ADD)

        self._interval_dd = T.dropdown_field(
            "Intervalo (s)", ["15", "30", "60", "120", "300"],
            value="60", width=140,
        )
        self._toggle_btn = T.primary_button("▶ Iniciar monitor", on_click=self._toggle, width=180)
        self._status_label = ft.Text("Monitor detenido", size=12, color=T.TEXT_MUTED)
        self._urls_col = ft.Column(spacing=6)
        self._refresh_urls()

        self.controls = [
            ft.Column([
                ft.Text("Monitor de URLs", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Comprueba la disponibilidad periódica de servicios web", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._url_field, self._alias_field, self._add_btn], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.END),
            ])),

            T.card(ft.Row([
                self._interval_dd,
                self._toggle_btn,
                self._status_label,
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)),

            ft.Text("URLs vigiladas", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._urls_col,
        ]

    def _refresh_urls(self):
        urls = db.get_monitor_urls()
        self._urls_col.controls.clear()
        if not urls:
            self._urls_col.controls.append(
                ft.Text("Sin URLs añadidas.", size=12, color=T.TEXT_MUTED)
            )
            return
        for u in urls:
            self._urls_col.controls.append(self._make_row(u))

    def _make_row(self, u):
        status = u.get("last_status", "pending")
        code = u.get("last_status_code") or 0
        ms = u.get("response_ms") or 0
        last = (u.get("last_check") or "")[:16].replace("T", " ")
        alias = u.get("alias") or u["url"]

        return T.card(ft.Row([
            ft.Column([
                ft.Text(alias, size=13, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text(u["url"], size=11, color=T.TEXT_MUTED),
            ], spacing=2, tight=True, expand=True),
            ft.Text(f"HTTP {code}" if code else "—", size=12, color=T.TEXT_SECONDARY, width=80),
            ft.Text(f"{ms:.0f} ms" if ms else "—", size=13, color=T.LIME, width=65),
            ft.Text(last or "Sin revisar", size=11, color=T.TEXT_MUTED, width=130),
            T.status_badge(status),
            T.icon_button(ft.icons.DELETE_OUTLINE, color=T.STATUS_DOWN,
                          on_click=lambda e, uid=u["id"]: self._delete(uid),
                          tooltip="Eliminar"),
        ], spacing=8))

    def _add_url(self, e):
        url = self._url_field.value.strip()
        if not url:
            self._url_field.error_text = "Introduce una URL"
            self.update()
            return
        self._url_field.error_text = None
        alias = self._alias_field.value.strip()
        db.add_monitor_url(url, alias)
        self._url_field.value = ""
        self._alias_field.value = ""
        self._refresh_urls()
        self.update()

    def _delete(self, uid):
        db.delete_monitor_url(uid)
        self._refresh_urls()
        self.update()

    def _toggle(self, e):
        if self._monitoring:
            self._monitoring = False
            self._toggle_btn.text = "▶ Iniciar monitor"
            self._toggle_btn.style = ft.ButtonStyle(
                bgcolor=T.LIME, color=T.DARK_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self._status_label.value = "Monitor detenido"
            self.update()
        else:
            self._monitoring = True
            self._toggle_btn.text = "⏹ Detener monitor"
            self._toggle_btn.style = ft.ButtonStyle(
                bgcolor=T.STATUS_DOWN, color=T.TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self._status_label.value = "Monitor activo…"
            self.update()
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        interval = int(self._interval_dd.value or 60)
        while self._monitoring:
            urls = db.get_monitor_urls()
            active = [u for u in urls if u.get("is_active", 1)]
            for u in active:
                if not self._monitoring:
                    break
                res = network.check_url(u["url"])
                db.update_monitor_status(u["url"], res["status"], res.get("code", 0), res["ms"])
            try:
                self._refresh_urls()
                down = sum(1 for u in db.get_monitor_urls() if u.get("last_status") == "down")
                self._status_label.value = f"Revisadas {len(active)} URLs · {down} caídas"
                self.update()
            except Exception:
                pass
            for _ in range(interval * 2):
                if not self._monitoring:
                    break
                time.sleep(0.5)

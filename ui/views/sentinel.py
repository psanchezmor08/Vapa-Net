"""
VapaNet — Vista Sentinel (vigilancia continua de hosts)
"""

import flet as ft
import threading
import time
from ui import theme as T
from core import db, network


class SentinelView(ft.Column):
    def __init__(self):
        super().__init__(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
        self._monitoring = False
        self._monitor_thread = None
        self._build()

    def _build(self):
        self._host_field = T.input_field("Host o IP", hint="192.168.1.1", expand=True)
        self._alias_field = T.input_field("Alias (opcional)", hint="Router principal", expand=True)
        self._add_btn = T.primary_button("Añadir", on_click=self._add_host, icon=ft.icons.ADD)

        self._interval_dd = T.dropdown_field(
            "Intervalo", ["10", "30", "60", "120", "300"],
            value="30", width=120,
            on_change=lambda e: None
        )
        self._toggle_btn = T.primary_button("▶ Iniciar monitor", on_click=self._toggle_monitor, width=180)
        self._status_label = ft.Text("Monitor detenido", size=12, color=T.TEXT_MUTED)

        self._hosts_col = ft.Column(spacing=6)
        self._refresh_hosts()

        self.controls = [
            ft.Column([
                ft.Text("Sentinel", size=22, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                ft.Text("Vigilancia continua con ping periódico a tus hosts", size=12, color=T.TEXT_SECONDARY),
            ], spacing=2, tight=True),

            T.card(ft.Column([
                ft.Row([self._host_field, self._alias_field, self._add_btn], spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.END),
            ], spacing=10)),

            T.card(ft.Column([
                ft.Row([
                    self._interval_dd,
                    self._toggle_btn,
                    self._status_label,
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ])),

            ft.Text("Hosts vigilados", size=14, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
            self._hosts_col,
        ]

    def _refresh_hosts(self):
        hosts = db.get_sentinel_hosts()
        self._hosts_col.controls.clear()
        if not hosts:
            self._hosts_col.controls.append(
                ft.Text("Sin hosts añadidos. Añade uno arriba.", size=12, color=T.TEXT_MUTED)
            )
            return
        for h in hosts:
            self._hosts_col.controls.append(self._make_host_row(h))

    def _make_host_row(self, h):
        status = h.get("last_status", "pending")
        ms = h.get("response_ms") or 0
        last = (h.get("last_check") or "")[:16].replace("T", " ")
        alias = h.get("alias") or h["host"]

        return T.card(
            ft.Row([
                ft.Column([
                    ft.Text(alias, size=13, weight=ft.FontWeight.W_500, color=T.TEXT_PRIMARY),
                    ft.Text(h["host"], size=11, color=T.TEXT_MUTED, font_family="Consolas"),
                ], spacing=2, tight=True, expand=True),
                ft.Text(f"{ms:.0f} ms" if ms else "—", size=13, color=T.LIME, width=70),
                ft.Text(last or "Sin revisar", size=11, color=T.TEXT_MUTED, width=130),
                T.status_badge(status),
                T.icon_button(ft.icons.DELETE_OUTLINE, color=T.STATUS_DOWN,
                              on_click=lambda e, hid=h["id"]: self._delete_host(hid),
                              tooltip="Eliminar"),
            ], spacing=10)
        )

    def _add_host(self, e):
        host = self._host_field.value.strip()
        if not host:
            self._host_field.error_text = "Introduce un host"
            self.update()
            return
        self._host_field.error_text = None
        alias = self._alias_field.value.strip()
        db.add_sentinel_host(host, alias)
        self._host_field.value = ""
        self._alias_field.value = ""
        self._refresh_hosts()
        self.update()

    def _delete_host(self, host_id: int):
        db.delete_sentinel_host(host_id)
        self._refresh_hosts()
        self.update()

    def _toggle_monitor(self, e):
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
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def _monitor_loop(self):
        interval = int(self._interval_dd.value or 30)
        while self._monitoring:
            hosts = db.get_sentinel_hosts()
            active = [h for h in hosts if h.get("is_active", 1)]
            for h in active:
                if not self._monitoring:
                    break
                res = network.ping_host(h["host"], count=1, timeout=2)
                db.update_sentinel_status(h["host"], res["status"], res["avg_ms"])
            try:
                self._refresh_hosts()
                down = sum(1 for h in db.get_sentinel_hosts() if h.get("last_status") == "down")
                self._status_label.value = (
                    f"Revisado {len(active)} hosts · {down} caídos — próxima revisión en {interval}s"
                )
                self.update()
            except Exception:
                pass
            # Sleep in chunks so we can interrupt
            for _ in range(interval * 2):
                if not self._monitoring:
                    break
                time.sleep(0.5)

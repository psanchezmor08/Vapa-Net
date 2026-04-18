"""
VapaNet — Sistema de diseño / tema visual
Paleta Vapa: verde lima sobre fondo azul-noche
Compatible con Flet 0.80+
"""

import flet as ft

# ──────────────────────────────────────────────
# PALETA DE COLORES
# ──────────────────────────────────────────────

LIME          = "#A8CC00"
LIME_BRIGHT   = "#C4F000"
LIME_MUTED    = "#6A8800"
LIME_DIM      = "#3D5000"

DARK_BG       = "#0B0D18"
DARK_SURFACE  = "#11152A"
DARK_PANEL    = "#181D36"
DARK_HOVER    = "#1E2440"
DARK_BORDER   = "#252C4A"
DARK_BORDER2  = "#2E3860"

TEXT_PRIMARY   = "#E2EBFF"
TEXT_SECONDARY = "#7A8BB0"
TEXT_MUTED     = "#4A5575"

STATUS_UP     = "#39D98A"
STATUS_DOWN   = "#FF5C5C"
STATUS_WARN   = "#F5A623"
STATUS_PEND   = "#7A8BB0"

# ──────────────────────────────────────────────
# HELPERS DE ESTILO
# ──────────────────────────────────────────────

def card(content, padding=16, border_color=DARK_BORDER) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=DARK_SURFACE,
        border=ft.Border.all(1, border_color),
        border_radius=10,
        padding=padding,
    )


def lime_card(content, padding=16) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=DARK_PANEL,
        border=ft.Border.all(1, LIME_DIM),
        border_radius=10,
        padding=padding,
    )


def section_title(text: str, subtitle: str = "") -> ft.Column:
    children = [
        ft.Text(text, size=18, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)
    ]
    if subtitle:
        children.append(ft.Text(subtitle, size=12, color=TEXT_SECONDARY))
    return ft.Column(children, spacing=2, tight=True)


def label(text: str, size: int = 12, color: str = TEXT_SECONDARY) -> ft.Text:
    return ft.Text(text, size=size, color=color)


def value_text(text: str, size: int = 24, color: str = LIME) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.W_500, color=color)


def metric_card(label_text: str, value: str, unit: str = "", trend: str = "") -> ft.Container:
    children = [
        ft.Text(label_text, size=11, color=TEXT_SECONDARY),
        ft.Row([
            ft.Text(value, size=22, weight=ft.FontWeight.W_500, color=LIME),
            ft.Text(unit, size=12, color=TEXT_MUTED),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.END),
    ]
    if trend:
        children.append(ft.Text(trend, size=11, color=LIME_MUTED))
    return ft.Container(
        content=ft.Column(children, spacing=4, tight=True),
        bgcolor=DARK_PANEL,
        border=ft.Border.all(1, DARK_BORDER),
        border_radius=8,
        padding=12,
        expand=True,
    )


def status_badge(status: str) -> ft.Container:
    colors = {
        "up":       (STATUS_UP,   "#0A2218"),
        "down":     (STATUS_DOWN, "#220A0A"),
        "degraded": (STATUS_WARN, "#221500"),
        "timeout":  (STATUS_WARN, "#221500"),
        "pending":  (TEXT_MUTED,  DARK_PANEL),
        "open":     (STATUS_UP,   "#0A2218"),
        "closed":   (TEXT_MUTED,  DARK_PANEL),
        "error":    (STATUS_DOWN, "#220A0A"),
    }
    fg, bg = colors.get(status.lower(), (TEXT_MUTED, DARK_PANEL))
    labels = {
        "up": "UP", "down": "DOWN", "degraded": "DEGRADED",
        "timeout": "TIMEOUT", "pending": "PENDIENTE",
        "open": "ABIERTO", "closed": "CERRADO", "error": "ERROR"
    }
    text = labels.get(status.lower(), status.upper())
    return ft.Container(
        content=ft.Text(text, size=10, weight=ft.FontWeight.W_500, color=fg),
        bgcolor=bg,
        border=ft.Border.all(1, fg + "44"),
        border_radius=5,
        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
    )


def primary_button(text: str, on_click=None, icon=None, width=None) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        bgcolor=LIME,
        color=DARK_BG,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            text_style=ft.TextStyle(weight=ft.FontWeight.W_500, size=13),
        ),
        width=width,
    )


def secondary_button(text: str, on_click=None, icon=None, width=None) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        content=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            side=ft.BorderSide(1, DARK_BORDER2),
            color=TEXT_SECONDARY,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        width=width,
    )


def icon_button(icon, on_click=None, tooltip="", color=TEXT_SECONDARY) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        on_click=on_click,
        tooltip=tooltip,
        icon_color=color,
        icon_size=18,
    )


def divider() -> ft.Divider:
    return ft.Divider(height=1, color=DARK_BORDER)


def mono_text(text: str, size: int = 12, color: str = TEXT_PRIMARY) -> ft.Text:
    return ft.Text(text, size=size, color=color, font_family="Consolas")


def alert_row(text: str, color: str = LIME) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Container(width=7, height=7, bgcolor=color, border_radius=4),
            ft.Text(text, size=12, color=TEXT_PRIMARY, expand=True),
        ], spacing=10),
        bgcolor=DARK_PANEL,
        border=ft.Border.all(1, color + "44"),
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
    )


def input_field(label_text: str, hint: str = "", value: str = "",
                on_change=None, expand=True, password=False) -> ft.TextField:
    return ft.TextField(
        label=label_text,
        hint_text=hint,
        value=value,
        on_change=on_change,
        password=password,
        bgcolor=DARK_PANEL,
        border_color=DARK_BORDER,
        focused_border_color=LIME,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        border_radius=8,
        content_padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        expand=expand,
    )


def dropdown_field(label_text: str, options: list, value: str = "",
                   on_change=None, width=None) -> ft.Dropdown:
    return ft.Dropdown(
        label=label_text,
        value=value,
        options=[ft.dropdown.Option(key=o, text=o) for o in options],
        on_select=on_change,
        bgcolor=DARK_PANEL,
        border_color=DARK_BORDER,
        focused_border_color=LIME,
        label_style=ft.TextStyle(color=TEXT_SECONDARY, size=12),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=13),
        border_radius=8,
        width=width,
    )


def progress_bar(value=None, color=LIME) -> ft.ProgressBar:
    return ft.ProgressBar(
        value=value,
        color=color,
        bgcolor=DARK_BORDER,
        border_radius=4,
        height=4,
    )


def nav_item(icon, label_text: str, active: bool = False, on_click=None, badge: int = 0) -> ft.Container:
    bg = DARK_HOVER if active else "transparent"
    color = LIME if active else TEXT_SECONDARY
    border = ft.Border.all(1, DARK_BORDER2) if active else ft.Border.all(1, "transparent")

    row_children = [
        ft.Icon(icon, size=16, color=color),
        ft.Text(label_text, size=13, color=color, expand=True),
    ]
    if badge > 0:
        row_children.append(
            ft.Container(
                content=ft.Text(str(badge), size=10, weight=ft.FontWeight.W_500, color=DARK_BG),
                bgcolor=LIME,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=6, vertical=1),
            )
        )

    return ft.Container(
        content=ft.Row(row_children, spacing=9),
        bgcolor=bg,
        border=border,
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        on_click=on_click,
        ink=True,
        margin=ft.Margin.only(bottom=1),
    )


def section_label(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(text.upper(), size=10, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
        padding=ft.Padding.only(left=8, top=10, bottom=4),
    )

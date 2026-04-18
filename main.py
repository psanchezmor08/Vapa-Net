"""
VapaNet — Network Intelligence Suite
Punto de entrada principal
"""

import flet as ft
from ui.app import VapaNetApp


def main(page: ft.Page):
    app = VapaNetApp(page)
    app.initialize()


if __name__ == "__main__":
    ft.run(main, name="VapaNet")

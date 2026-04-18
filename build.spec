# -*- mode: python ; coding: utf-8 -*-
# VapaNet — build.spec
# Uso: pyinstaller build.spec

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Recoge todos los submodulos de flet
flet_hidden = collect_submodules('flet')
flet_data   = collect_data_files('flet')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=flet_data + [
        ('assets', 'assets'),
    ],
    hiddenimports=flet_hidden + [
        'flet_core',
        'flet_runtime',
        'flet_desktop',
        'sqlite3',
        'threading',
        'subprocess',
        'socket',
        'platform',
        'urllib.request',
        'urllib.error',
        'json',
        'os',
        're',
        'time',
        'struct',
        'core.db',
        'core.network',
        'ui.app',
        'ui.theme',
        'ui.views.dashboard',
        'ui.views.speedtest',
        'ui.views.ping',
        'ui.views.ports',
        'ui.views.dns',
        'ui.views.traceroute',
        'ui.views.batch',
        'ui.views.sentinel',
        'ui.views.monitor',
        'ui.views.subnet',
        'ui.views.whois',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VapaNet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

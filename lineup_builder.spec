# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files
import os

# Pull in every asset / hidden import needed by customtkinter and iconipy
ctk_datas,    ctk_bins,    ctk_hidden    = collect_all('customtkinter')
iconipy_datas, iconipy_bins, iconipy_hidden = collect_all('iconipy')

# tkcalendar needs babel locale data at runtime
babel_datas = collect_data_files('babel')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ctk_bins + iconipy_bins,
    datas=(
        ctk_datas
        + iconipy_datas
        + babel_datas
    ),
    hiddenimports=(
        ctk_hidden
        + iconipy_hidden
        + [
            'tkcalendar',
            'babel',
            'babel.numbers',
            'babel.dates',
            'yaml',
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name='LineupBuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

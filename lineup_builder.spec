# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# DearPyGui bundles its own native binaries — collect everything
dpg_datas, dpg_bins, dpg_hidden = collect_all('dearpygui')

# Runtime data files bundled alongside the executable
runtime_datas = [
    ('lineup_library.yaml', '.'),
    ('lineup_events.yaml',  '.'),
    ('settings.json',       '.'),
    ('window_state.json',   '.'),
    ('auto_save.json',      '.'),
    ('assets',              'assets'),
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=dpg_bins,
    datas=dpg_datas + runtime_datas,
    hiddenimports=dpg_hidden + [
        'yaml',
        # src package tree
        'src',
        'src.backend',
        'src.backend.data_manager',
        'src.backend.debounce',
        'src.backend.event_bus',
        'src.backend.lineup_model',
        'src.backend.output_builder',
        'src.backend.output_generator',
        'src.backend.types',
        'src.frontend',
        'src.frontend.app',
        'src.frontend.date_time_picker',
        'src.frontend.roster',
        'src.frontend.drag_drop',
        'src.frontend.events_manager',
        'src.frontend.fonts',
        'src.frontend.genre_manager',
        'src.frontend.import_parser',
        'src.frontend.settings_manager',
        'src.frontend.slot_manager',
        'src.frontend.slot_ui',
        'src.frontend.theme',
        'src.frontend.types',
        'src.frontend.ui_builder',
        'src.frontend.utils',
        'src.frontend.widgets',
    ],
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
    icon='assets/icon.ico',
)
